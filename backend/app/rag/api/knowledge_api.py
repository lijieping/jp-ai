import traceback
from typing import List

from fastapi import APIRouter, File, UploadFile, Path, Request, Form

from app.common.api import R
from app.infra import logger
from app.rag.service import knowledge_service, rag_pipeline_service
from app.rag.schemas import KbSpaceIn

router = APIRouter(prefix="/kb", tags=["kb"])

@router.post("/space", summary="创建业务空间")
def space_create(body:KbSpaceIn):
    # 修复字段名匹配问题
    id = knowledge_service.space_create(body.name, body.desc, body.collection)
    return R.ok(id)

@router.get("/space/list", summary="获取所有业务空间列表")
def space_list_all():
    """获取所有知识库空间列表的接口"""
    kb_spaces = knowledge_service.space_list_all()
    return R.ok(kb_spaces)

@router.get("/space/{space_id}", summary="获取业务空间详情")
def space_get_by_id(space_id: int = Path(..., description="业务空间ID")):
    """根据ID获取单个业务空间详情"""
    try:
        space = knowledge_service.space_get_by_id(space_id)
        return R.ok(space)
    except ValueError as e:
        return R.fail(str(e))
    except Exception as e:
        logger.error(traceback.format_exc())
        return R.fail(msg = "获取业务空间失败")

@router.delete("/space/{space_id}", summary="删除业务空间")
def space_delete(space_id: int = Path(..., description="业务空间ID")):
    """删除指定ID的业务空间"""
    try:
        knowledge_service.space_delete(space_id)
        return R.ok(msg="业务空间删除成功")
    except ValueError as e:
        return R.fail(msg = str(e))
    except Exception as e:
        logger.error(traceback.format_exc())
        return R.fail(msg = "删除业务空间失败")

@router.put("/space/{space_id}", summary="更新业务空间信息")
def space_update(
    body:KbSpaceIn,
    space_id: int = Path(..., description="业务空间ID")
):
    """更新指定业务空间的信息"""
    try:
        knowledge_service.space_update(space_id, body)
        return R.ok(msg="业务空间更新成功")
    except ValueError as e:
        return R.fail(str(e))
    except Exception as e:
        logger.error(traceback.format_exc())
        return R.fail("更新业务空间失败")

@router.post("/space/{space_id}/file", summary="上传文件到知识库空间")
def file_upload(
    request: Request,
    space_id: int = Path(..., description="知识库空间ID"),
    files: List[UploadFile] = File(..., description="要上传的文件"),
    description: str = Form("", description="文件描述")
):
    """上传文件到指定的知识库空间"""
    try:
        # 调用服务层方法处理文件上传，传入用户ID和描述
        result = knowledge_service.file_upload(space_id, files, request.state.user_id, description=description)
        return R.ok(result)
    except ValueError as e:
        # 处理知识库空间不存在的情况
        return R.fail(str(e))
    except Exception as e:
        # 处理其他可能的异常
        return R.fail(f"文件上传失败: {str(e)}")

@router.get("/file/list", summary="获取知识库空间文件列表")
def file_list(
    spaceId: int,
    pageSize: int = 10,
    curPage: int = 1
):
    """获取知识库空间中的文件列表，支持分页查询"""
    try:
        # 调用服务层方法获取文件列表，传入分页参数
        result = knowledge_service.file_with_rag_info_list(spaceId, page_size=pageSize, cur_page=curPage)
        return R.ok(result)
    except Exception as e:
        # 处理其他可能的异常
        logger.info(traceback.format_exc())
        return R.fail(msg = "获取文件列表失败")

@router.delete("/file/{file_id}", summary="删除文件")
def file_delete(file_id: int = Path(..., description="文件id")):
    # todo kb_service:从向量库删除，如果有流水线正在执行任务，需要检索record表的状态置为中断，涉及到先后顺序问题 ？ 先等pipeline执行完成， 再删除， pipeline用队列，同一知识文件的操作的放到同一队列，保证安全
    # todo rag_pipeline_service:任务结束，发现状态是中断，则不落向量库
    try:
        knowledge_service.file_delete(file_id)
    except Exception as e:
        return R.fail(str(e))
    return R.ok()

@router.get("/rag/pipeline/file-types", summary="获取rag支持的文件类型")
def rag_file_type_lists():
    return R.ok(rag_pipeline_service.get_support_exts())

