from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    external_id: str
    name: str
    image_url: str  # Url where the image is located

    is_approx_size: bool  # true -> If size is an approx
    size_format: str  # "kg" -> Format of the size

    price: float  # "3.37" -> Total price
    price_per_size: float  # "8.43" -> Price per whole size
    is_pack: bool  # true -> If unit contains multiple units

    brand: str | None = None
    size: float | None = None  # 0.4 -> Total size of the product
    packaging: str | None = None  # "Pack-2", "Garrafa"... -> Type of packaging
    total_units: int | None = None  # 2 -> Number of units in pack
    unit_name: str | None = None  # "paquetes" -> Name of the unit


@dataclass(frozen=True)
class Subtype:
    external_id: str
    name: str
    products: list[Product]


@dataclass(frozen=True)
class Subcategory:
    external_id: str
    name: str
    subtypes: list[Subtype]


@dataclass(frozen=True)
class Category:
    external_id: str
    name: str
    subcategories: list[Subcategory]


@dataclass(frozen=True)
class Department:
    external_id: str
    name: str
    categories: list[Category]
