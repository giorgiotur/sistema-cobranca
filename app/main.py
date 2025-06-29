from fastapi import FastAPI
from app import models, database
from app.routes import users, pacotes, login, ativacao, hoteis
from app import clientes
from app.routes import orcamento_pre_pago_routes
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from app.routes import reservas_routes
from app.routes.empresa_routes import router as empresa_router


# ✅ Instancia o app com metadados
app = FastAPI(
    title="Sistema de Cobrança Pré-Paga",
    description="API para gerenciar pacotes de viagem, usuários e cobranças.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Usuários", "description": "Cadastro e autenticação de usuários"},
        {"name": "Pacotes", "description": "Gerenciamento de pacotes turísticos"},
        {"name": "Hoteis", "description": "Cadastro e descrição de hotéis"},
    ],
    swagger_ui_init_oauth={
        "clientId": "swagger-ui",
        "usePkceWithAuthorizationCodeGrant": False,
        "scopes": {}
    }
)

# ✅ Cria as tabelas no banco
models.Base.metadata.create_all(bind=database.engine)

# ✅ Registra todos os routers (ordem organizada)
app.include_router(users.router)
app.include_router(pacotes.router)
app.include_router(login.router)
app.include_router(ativacao.router)
app.include_router(clientes.router)
app.include_router(hoteis.router)
app.include_router(orcamento_pre_pago_routes.router, prefix="/orcamentos/pre-pago", tags=["orcamentos"])
app.include_router(reservas_routes.router)
app.include_router(empresa_router, prefix="/empresas", tags=["Empresas"]) 

# ✅ Rota base de teste
@app.get("/")
def root():
    return {"msg": "API online"}

# ✅ Habilitar o FastAPI a servir arquivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ✅ Habilitar esquema de segurança Bearer Token no Swagger
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Sistema de Cobrança Pré-Paga",
        version="1.0.0",
        description="API para gerenciar pacotes de viagem, usuários e cobranças.",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
