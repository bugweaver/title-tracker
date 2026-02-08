from auth.controller import AuthController
from titles.controller import TitleController
from games.controller import GamesController

from search.controller import SearchController
from user_titles.controller import UserTitlesController
from users.controller import UsersController
from backup.controller import BackupController
from auth.jwt import jwt_config
import os
import mimetypes
from litestar.static_files import StaticFilesConfig
import mimetypes

# Ensure mime types are loaded
mimetypes.init()
mimetypes.add_type("image/jpeg", ".jpg")
mimetypes.add_type("image/jpeg", ".jpeg")
mimetypes.add_type("image/png", ".png")

# CORS configuration for development
cors_config = CORSConfig(
    allow_origins=["http://localhost", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Собираем роутер API
api_router = Router(path="/api/v1", route_handlers=[
    AuthController, 
    TitleController, 
    GamesController,

    SearchController,
    UserTitlesController,
    UsersController,
    BackupController,
])


# ... (imports)

app = Litestar(
    route_handlers=[api_router],
    on_app_init=[jwt_config.on_app_init],
    on_shutdown=[db_helper.dispose],
    cors_config=cors_config,
    static_files_config=[
        StaticFilesConfig(directories=[os.path.join(os.path.dirname(__file__), "..", "static")], path="/static"),
    ],
)

