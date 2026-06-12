"""
Schema do Helfy (SCRUM-20, spec §5).

Enums de domínio (goal, diet_type, source...) são colunas String validadas na
borda Pydantic — evita migrations a cada novo valor durante a sprint.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core_api.db.base import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())
    profile: Mapped["Profile | None"] = relationship(back_populates="user",
                                                     cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                               primary_key=True)
    age: Mapped[int | None] = mapped_column(Integer)
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    goal: Mapped[str | None] = mapped_column(String(20))
    diet_type: Mapped[str | None] = mapped_column(String(20))
    activity_level: Mapped[str | None] = mapped_column(String(20))
    cholesterol: Mapped[int | None] = mapped_column(Integer)
    glucose: Mapped[int | None] = mapped_column(Integer)
    restrictions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    preferences: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    allergies: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now(),
                                                 onupdate=func.now())
    user: Mapped[User] = relationship(back_populates="profile")


class Food(Base):
    __tablename__ = "foods"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          default=uuid.uuid4)
    barcode: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    food_group: Mapped[str] = mapped_column(String(40), default="other")
    nutrition: Mapped[dict] = mapped_column(JSONB, default=dict)
    allergen_flags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    flags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    source: Mapped[str] = mapped_column(String(10), default="MANUAL")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())


class PantryItem(Base):
    __tablename__ = "pantry_items"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                               primary_key=True)
    food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"),
                                               primary_key=True)
    quantity: Mapped[float | None] = mapped_column(Numeric(10, 2))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())


class Recipe(Base):
    __tablename__ = "recipes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    instructions: Mapped[str] = mapped_column(Text)
    nutrition_total: Mapped[dict] = mapped_column(JSONB, default=dict)
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        cascade="all, delete-orphan")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True)
    food_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), primary_key=True)
    quantity: Mapped[str | None] = mapped_column(String(60))


class FoodScore(Base):
    __tablename__ = "food_scores"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                               primary_key=True)
    food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"),
                                               primary_key=True)
    score: Mapped[float] = mapped_column(Numeric(4, 3))
    breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)
    model_version: Mapped[str] = mapped_column(String(20))
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now())
