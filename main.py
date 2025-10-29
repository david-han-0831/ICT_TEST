from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# FastAPI 앱 생성
app = FastAPI(
    title="FastAPI Swagger 예제",
    description="Swagger 문서 확인을 위한 간단한 API 예제",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI 경로
    redoc_url="/redoc"  # ReDoc 경로
)

# Enum 모델 정의
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

# Pydantic 모델 정의
class User(BaseModel):
    id: int = Field(..., description="사용자 고유 ID")
    name: str = Field(..., min_length=2, max_length=50, description="사용자 이름")
    email: str = Field(..., description="이메일 주소")
    age: Optional[int] = Field(None, ge=0, le=120, description="나이 (0-120)")
    role: UserRole = Field(default=UserRole.USER, description="사용자 역할")
    is_active: bool = Field(default=True, description="활성 상태")

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., description="이메일 주소")
    age: Optional[int] = Field(None, ge=0, le=120)
    role: UserRole = Field(default=UserRole.USER)

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=120)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class Message(BaseModel):
    message: str = Field(..., description="응답 메시지")
    status_code: int = Field(..., description="HTTP 상태 코드")

# 가상의 데이터베이스
users_db = [
    User(id=1, name="김철수", email="kim@example.com", age=25, role=UserRole.USER),
    User(id=2, name="이영희", email="lee@example.com", age=30, role=UserRole.ADMIN),
    User(id=3, name="박민수", email="park@example.com", age=22, role=UserRole.USER),
]

# 루트 엔드포인트
@app.get("/", tags=["기본"])
async def root():
    """
    루트 엔드포인트 - API 정보를 반환합니다.
    """
    return {
        "message": "FastAPI Swagger 예제에 오신 것을 환영합니다!",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# 사용자 관련 엔드포인트들
@app.get("/users", response_model=List[User], tags=["사용자 관리"])
async def get_users():
    """
    모든 사용자 목록을 조회합니다.
    """
    return users_db

@app.get("/users/{user_id}", response_model=User, tags=["사용자 관리"])
async def get_user(user_id: int):
    """
    특정 사용자 정보를 조회합니다.
    
    - **user_id**: 조회할 사용자의 ID
    """
    user = next((user for user in users_db if user.id == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user

@app.post("/users", response_model=User, tags=["사용자 관리"])
async def create_user(user: UserCreate):
    """
    새로운 사용자를 생성합니다.
    
    - **name**: 사용자 이름 (2-50자)
    - **email**: 이메일 주소
    - **age**: 나이 (선택사항, 0-120)
    - **role**: 사용자 역할 (기본값: user)
    """
    new_id = max([u.id for u in users_db]) + 1 if users_db else 1
    new_user = User(id=new_id, **user.dict())
    users_db.append(new_user)
    return new_user

@app.put("/users/{user_id}", response_model=User, tags=["사용자 관리"])
async def update_user(user_id: int, user_update: UserUpdate):
    """
    기존 사용자 정보를 수정합니다.
    """
    user_index = next((i for i, user in enumerate(users_db) if user.id == user_id), None)
    if user_index is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    existing_user = users_db[user_index]
    update_data = user_update.dict(exclude_unset=True)
    updated_user = existing_user.copy(update=update_data)
    users_db[user_index] = updated_user
    return updated_user

@app.delete("/users/{user_id}", response_model=Message, tags=["사용자 관리"])
async def delete_user(user_id: int):
    """
    사용자를 삭제합니다.
    """
    user_index = next((i for i, user in enumerate(users_db) if user.id == user_id), None)
    if user_index is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    users_db.pop(user_index)
    return Message(message=f"사용자 ID {user_id}가 삭제되었습니다", status_code=200)

# 검색 및 필터링 엔드포인트
@app.get("/users/search/", response_model=List[User], tags=["검색"])
async def search_users(
    name: Optional[str] = None,
    role: Optional[UserRole] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None
):
    """
    사용자를 검색합니다.
    
    - **name**: 이름으로 검색 (부분 일치)
    - **role**: 역할로 필터링
    - **min_age**: 최소 나이
    - **max_age**: 최대 나이
    """
    filtered_users = users_db.copy()
    
    if name:
        filtered_users = [u for u in filtered_users if name.lower() in u.name.lower()]
    
    if role:
        filtered_users = [u for u in filtered_users if u.role == role]
    
    if min_age is not None:
        filtered_users = [u for u in filtered_users if u.age and u.age >= min_age]
    
    if max_age is not None:
        filtered_users = [u for u in filtered_users if u.age and u.age <= max_age]
    
    return filtered_users

# 통계 엔드포인트
@app.get("/stats", tags=["통계"])
async def get_stats():
    """
    사용자 통계 정보를 반환합니다.
    """
    total_users = len(users_db)
    active_users = len([u for u in users_db if u.is_active])
    role_counts = {}
    for user in users_db:
        role_counts[user.role] = role_counts.get(user.role, 0) + 1
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "role_distribution": role_counts
    }

# 헬스 체크 엔드포인트
@app.get("/health", tags=["시스템"])
async def health_check():
    """
    API 서버 상태를 확인합니다.
    """
    return {"status": "healthy", "message": "서버가 정상적으로 작동 중입니다"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
