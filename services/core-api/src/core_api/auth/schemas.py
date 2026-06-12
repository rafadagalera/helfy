from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr = Field(description="E-mail único do usuário (usado para login)")
    password: str = Field(min_length=8, description="Senha com no mínimo 8 caracteres")
    name: str = Field(min_length=1, max_length=120, description="Nome de exibição")


class LoginIn(BaseModel):
    email: EmailStr = Field(description="E-mail cadastrado")
    password: str = Field(description="Senha do usuário")


class UserOut(BaseModel):
    id: str = Field(description="UUID do usuário")
    email: EmailStr = Field(description="E-mail do usuário")
    name: str = Field(description="Nome de exibição")


class TokenOut(BaseModel):
    access_token: str = Field(description="JWT Bearer token; expira em 24h por padrão")
    token_type: str = Field(default="bearer", description="Tipo de token (sempre 'bearer')")
