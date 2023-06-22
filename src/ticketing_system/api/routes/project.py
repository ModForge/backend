from fastapi import APIRouter, Request, HTTPException
from bson import ObjectId
from .. import utils
from .. import webhooks
import traceback
import time
import urllib.parse

router = APIRouter(prefix="/api")
db = utils.get_db_client()


@router.put("/project")
async def create_project(request: Request):
    req_info = await request.json()

    find_project = db.projects.find_one({"name": req_info["name"]})
    print(req_info)

    if not find_project:
        try:
            project = db.projects.insert_one(req_info)
            return utils.json_ready(req_info["name"])

        except:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=503, detail="Unable write issue to database"
            )

    elif find_project:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=400,
            detail="This project already exists, please enter a unique project name",
        )
    else:
        raise HTTPException(status_code=503, detail="Unable write issue to database")


@router.get("/projects/")
async def get_all_projects():
    projects = list(db.projects.find())
    return utils.prepare_json(projects)


@router.get("/project/{project_id}")
async def get_project(project_id):
    project = db.projects.find_one({"_id": ObjectId(project_id)})

    if project:
        return utils.prepare_json(
            {
                **project,
                # TODO: use project id for fetching discord bot
                # "webhooks": [i for i in db.webhooks.find({"name": project["name"]})],
            }
        )


@router.put("/project/webhooks")
async def create_project_webhook(request: Request):
    req_info = await request.json()
    proj_name = req_info["project_name"]
    time.sleep(0.5)

    find_project = db.projects.find_one({"name": proj_name})

    if find_project and db.webhooks.find_one({"url": req_info}):
        raise HTTPException(status_code=403, detail="webhook already exists")
    elif find_project and not db.webhooks.find_one({"url": req_info}):
        try:
            new_webhook = db.webhooks.insert_one(req_info)
        except:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=503, detail="Unable write issue to database"
            )

    elif not find_project:
        raise HTTPException(
            status_code=404,
            detail=f"Project not found, cannot write to database",
        )

    else:
        raise HTTPException(
            status_code=503,
            detail=f"Unable write webhook for channel to database",
        )


@router.put("/project/members/waitlist")
async def members_waitlist(request: Request):
    req_info = await request.json()
    find_project = db.projects.find_one({"name": req_info["project_name"]})

    if find_project and req_info["discord_id"] not in find_project:
        db.projects.update_one(
            {"name": req_info["project_name"]},
            {"$push": {"members": req_info["discord_id"]}},
        )
    elif find_project and req_info["discord_id"] in find_project:
        raise HTTPException(
            status_code=404,
            detail=f"User already a member of this project",
        )


@router.get("/project/{name}/categories")
async def create_categories(name: str):
    project = db.projects.find_one({"name": name})

    if not project:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to retrieve categories from database",
        )

    return utils.prepare_json(project["categories"])


@router.put("/project/{name}/categories")
async def create_categories(request: Request, name: str):
    req_info = await request.json()

    project = db.project.find({"name": name})
    if project:
        for category in req_info:
            db.projects.update_one(
                {"name": name},
                {"$push": {"categories": category.strip()}},
            )
    else:
        raise HTTPException(
            status_code=503,
            detail=f"Unable write to database",
        )


# @router.get("/project/{name}/issues")
# async def get_exact(name: str):
#     return utils.prepare_json(db.projects.find({"name": name}))


@router.get("/project/{project_name}/category/{category}/issues")
async def get_all_by_category(project_name: str, category: str):
    # issues = list(db.issues.find({"project_name": project_name, "category": category}))
    issues = db.issues.find(
        {"category": urllib.parse.unquote(category)}, {"modlogs": 0}
    )
    return utils.prepare_json(issues)


# @router.get("/category/{category}/issues")
# async def get_all_by_category(category: str):
#     issues = list(db.issues.find({"category": category}))
#     return utils.prepare_json(issues)
