"""
Hiring Assistant Agent (Supervisor)
Orchestrates the multi-step AI workflow:
  1. Parse resumes for candidates
  2. Match candidates against job requirements
  3. Generate outreach drafts for top matches
  4. Wait for human approval before finalizing

Publishes intermediate results to Kafka ai.results topic.
"""

import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from database import SessionLocal, mongo_db
from models.job import JobPosting
from models.application import Application
from models.member import Member
from agents.resume_parser import parse_resume_with_ollama
from agents.job_matcher import match_candidate_to_job
from agents.outreach_generator import generate_outreach_with_ollama
from kafka_producer import kafka_producer

logger = logging.getLogger(__name__)

# In-memory task store for active tasks (backed by MongoDB for persistence)
active_tasks: Dict[str, Dict[str, Any]] = {}
# WebSocket connections for streaming updates
ws_connections: Dict[str, list] = {}


async def update_task_status(
    task_id: str, status: str, step: str, data: Any = None, progress: int = 0
):
    """Update task status in memory, MongoDB, and notify WebSocket clients."""
    update = {
        "status": status,
        "current_step": step,
        "progress": progress,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if data:
        update["step_data"] = data

    # Update in-memory
    if task_id in active_tasks:
        active_tasks[task_id].update(update)
        if "steps" not in active_tasks[task_id]:
            active_tasks[task_id]["steps"] = []
        active_tasks[task_id]["steps"].append(
            {"step": step, "status": status, "timestamp": update["updated_at"]}
        )

    # Persist to MongoDB for observability
    await mongo_db.agent_tasks.update_one(
        {"task_id": task_id},
        {"$set": update, "$push": {"steps": {"step": step, "status": status, "timestamp": update["updated_at"]}}},
        upsert=True,
    )

    # Notify WebSocket clients
    if task_id in ws_connections:
        message = {"task_id": task_id, **update}
        for ws in ws_connections[task_id]:
            try:
                await ws.send_json(message)
            except Exception:
                pass

    # Publish to Kafka
    try:
        await kafka_producer.publish(
            topic="ai.results",
            event_type="ai.step_completed",
            actor_id="hiring_assistant",
            entity_type="ai_task",
            entity_id=task_id,
            payload={"step": step, "status": status, "progress": progress},
            trace_id=task_id,
        )
    except Exception:
        pass


async def run_hiring_workflow(task_id: str, job_id: int, top_n: int = 5):
    """
    Main hiring assistant workflow:
    1. Fetch job posting and candidates
    2. Parse resumes
    3. Match candidates to job
    4. Rank and shortlist top N
    5. Generate outreach drafts
    6. Wait for recruiter approval
    """
    db = SessionLocal()

    try:
        # ── Step 1: Fetch job and candidates ────────────────
        await update_task_status(task_id, "running", "fetch_data", progress=10)

        job = db.query(JobPosting).filter(JobPosting.job_id == job_id).first()
        if not job:
            await update_task_status(task_id, "failed", "fetch_data", data={"error": "Job not found"})
            return

        # Get all applicants for this job
        applications = db.query(Application).filter(Application.job_id == job_id).all()
        if not applications:
            # If no applications, get members with matching skills
            members = db.query(Member).limit(50).all()
        else:
            member_ids = [app.member_id for app in applications]
            members = db.query(Member).filter(Member.member_id.in_(member_ids)).all()

        if not members:
            await update_task_status(
                task_id, "failed", "fetch_data",
                data={"error": "No candidates found"},
            )
            return

        job_data = job.to_dict()
        await update_task_status(
            task_id, "running", "fetch_data",
            data={"job_title": job.title, "candidates_found": len(members)},
            progress=20,
        )

        # ── Step 2: Parse resumes ───────────────────────────
        await update_task_status(task_id, "running", "parse_resumes", progress=30)

        parsed_resumes = {}
        for i, member in enumerate(members):
            resume_text = member.resume_text or member.about or ""
            if resume_text:
                parsed = await parse_resume_with_ollama(resume_text)
                parsed_resumes[member.member_id] = parsed

            # Log trace
            await mongo_db.agent_traces.insert_one({
                "task_id": task_id,
                "step": "resume_parser",
                "member_id": member.member_id,
                "result": parsed_resumes.get(member.member_id, {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        await update_task_status(
            task_id, "running", "parse_resumes",
            data={"resumes_parsed": len(parsed_resumes)},
            progress=50,
        )

        # ── Step 3: Match candidates ────────────────────────
        await update_task_status(task_id, "running", "match_candidates", progress=60)

        match_results = []
        for member in members:
            candidate_data = member.to_dict()
            parsed = parsed_resumes.get(member.member_id)
            match = await match_candidate_to_job(job_data, candidate_data, parsed)
            match_results.append(match)

            await mongo_db.agent_traces.insert_one({
                "task_id": task_id,
                "step": "job_matcher",
                "member_id": member.member_id,
                "match_score": match["overall_score"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # Sort by score and take top N
        match_results.sort(key=lambda x: x["overall_score"], reverse=True)
        shortlist = match_results[:top_n]

        await update_task_status(
            task_id, "running", "match_candidates",
            data={
                "total_matched": len(match_results),
                "shortlist_count": len(shortlist),
                "top_score": shortlist[0]["overall_score"] if shortlist else 0,
            },
            progress=75,
        )

        # ── Step 4: Generate outreach drafts ─────────────────
        await update_task_status(task_id, "running", "generate_outreach", progress=85)

        outreach_drafts = []
        for match in shortlist:
            candidate_id = match["candidate_id"]
            member = db.query(Member).filter(Member.member_id == candidate_id).first()
            if member:
                outreach = await generate_outreach_with_ollama(
                    job_data, member.to_dict(), match
                )
                outreach["match_score"] = match["overall_score"]
                outreach["recommendation"] = match["recommendation"]
                outreach_drafts.append(outreach)

        await update_task_status(
            task_id, "running", "generate_outreach",
            data={"drafts_generated": len(outreach_drafts)},
            progress=90,
        )

        # ── Step 5: Ready for approval ───────────────────────
        final_result = {
            "job": {"job_id": job_id, "title": job.title},
            "shortlist": shortlist,
            "outreach_drafts": outreach_drafts,
            "total_candidates_analyzed": len(members),
        }

        active_tasks[task_id]["result"] = final_result

        await update_task_status(
            task_id, "awaiting_approval", "complete",
            data=final_result,
            progress=100,
        )

        # Publish final result to Kafka
        try:
            await kafka_producer.publish(
                topic="ai.results",
                event_type="ai.completed",
                actor_id="hiring_assistant",
                entity_type="ai_task",
                entity_id=task_id,
                payload={
                    "job_id": job_id,
                    "shortlist_count": len(shortlist),
                    "status": "awaiting_approval",
                },
                trace_id=task_id,
            )
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Hiring workflow failed: {e}", exc_info=True)
        await update_task_status(
            task_id, "failed", "error",
            data={"error": str(e)},
        )
    finally:
        db.close()


async def start_task(job_id: int, top_n: int = 5) -> str:
    """Start a new hiring assistant task and return the task_id."""
    task_id = str(uuid.uuid4())

    active_tasks[task_id] = {
        "task_id": task_id,
        "job_id": job_id,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "steps": [],
    }

    # Publish to Kafka
    try:
        await kafka_producer.publish(
            topic="ai.requests",
            event_type="ai.requested",
            actor_id="recruiter",
            entity_type="ai_task",
            entity_id=task_id,
            payload={"job_id": job_id, "top_n": top_n},
            trace_id=task_id,
        )
    except Exception:
        pass

    # Start the workflow as a background task
    asyncio.create_task(run_hiring_workflow(task_id, job_id, top_n))

    return task_id


def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Get the current status of a task."""
    return active_tasks.get(task_id)


async def approve_task(task_id: str, approved: bool, feedback: str = "") -> Dict[str, Any]:
    """Human-in-the-loop: approve or reject the AI output."""
    task = active_tasks.get(task_id)
    if not task:
        return {"success": False, "message": "Task not found"}

    if task["status"] != "awaiting_approval":
        return {"success": False, "message": f"Task is in '{task['status']}' state, not awaiting approval"}

    new_status = "approved" if approved else "rejected"
    task["status"] = new_status
    task["approval_feedback"] = feedback

    await update_task_status(
        task_id, new_status, "approval",
        data={"approved": approved, "feedback": feedback},
    )

    return {"success": True, "message": f"Task {new_status}", "task_id": task_id}
