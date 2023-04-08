import dataclasses
from http import client as http_client

import pandas as pd
import requests

from api_dataclasses import Category, Product, Subcategory, Subtype

CSV_FILEPATH = "final_products.csv"
GET_PRODUCTS_TO_CSV = True


class InvalidStatusCode(Exception):
    """
    Raised when the response code was not expected
    """


class MercadonaAPI:
    VENDOR_NAME = "Mercadona"
    BASE_URL = "https://tienda.mercadona.es/api/"

    def __init__(self, lang: str = "es", location: str = "vlc1") -> None:
        self.lang = lang
        self.wh = location

        self.categories: list[Category] = list()
        self.subcategories: list[Subcategory] = list()
        self.subtypes: list[Subtype] = list()
        self.products: list[Product] = list()

    @classmethod
    def export_products_to_csv(cls, file_url: str) -> None:
        api = cls()
        api._get_categories()
        products_df = api._generate_dataframe()

        print("Exporting to csv...")
        products_df.to_csv(file_url, index=False)

    def get(
        self, url: str, valid_status_codes: tuple[int, ...] = (http_client.OK,)
    ) -> dict:
        request_url = f"{self.BASE_URL}/{url}/"
        params = {"lang": self.lang, "wh": self.wh}

        request = requests.get(request_url, params=params)
        if request.status_code not in valid_status_codes:
            print("Maximum request limit reached! Please wait a couple seconds.")
            raise InvalidStatusCode(f"Unexpected status code {request.status_code}")

        return request.json()

    def _process_product(self, product_info: dict) -> Product:
        external_id = product_info["id"]
        name = product_info["display_name"]
        packaging = product_info["packaging"]
        image_url = product_info["thumbnail"]
        price_instructions = product_info["price_instructions"]

        size = (
            float(price_instructions["unit_size"])
            if price_instructions["unit_size"]
            else None
        )
        is_approx_size = bool(price_instructions["approx_size"])
        size_format = price_instructions["size_format"]

        price = float(price_instructions["unit_price"])
        price_per_size = float(price_instructions["bulk_price"])
        is_pack = bool(price_instructions["is_pack"])
        total_units = (
            int(price_instructions["total_units"])
            if price_instructions["total_units"]
            else None
        )
        unit_name = price_instructions["unit_name"]

        product = Product(
            external_id=external_id,
            name=name,
            packaging=packaging,
            image_url=image_url,
            size=size,
            is_approx_size=is_approx_size,
            size_format=size_format,
            price=price,
            price_per_size=price_per_size,
            is_pack=is_pack,
            total_units=total_units,
            unit_name=unit_name,
        )
        self.products.append(product)

        return product

    def _process_subtype(self, subtype_info: dict) -> Subtype:
        external_id = subtype_info["id"]
        name = subtype_info["name"]

        print(f"Getting products for {name}...")
        products_info = subtype_info["products"]
        products = list(map(self._process_product, products_info))

        subtype = Subtype(external_id=external_id, name=name, products=products)
        self.subtypes.append(subtype)

        return subtype

    def _get_subtypes(self, subcategory_id: str) -> list[Subtype]:
        subtypes_infos = self.get(f"categories/{subcategory_id}")["categories"]
        subtypes: list[Subtype] = list(map(self._process_subtype, subtypes_infos))

        return subtypes

    def _process_subcategory(self, subcategory_info: dict) -> Subcategory:
        external_id = subcategory_info["id"]
        name = subcategory_info["name"]

        print(f"Getting subtypes for {name}...")
        subtypes = self._get_subtypes(external_id)

        subcategory = Subcategory(external_id=external_id, name=name, subtypes=subtypes)
        self.subcategories.append(subcategory)

        return subcategory

    def _process_category(self, category_info: dict) -> Category:
        external_id = category_info["id"]
        name = category_info["name"]

        print(f"Getting subcategories for {name}...")
        subcategories_info = category_info["categories"]
        subcategories = list(map(self._process_subcategory, subcategories_info))

        category = Category(
            external_id=external_id, name=name, subcategories=subcategories
        )
        self.categories.append(category)

        return category

    def _get_categories(self) -> list[Category]:
        print("Getting categories...")
        categories_info = self.get("categories")["results"]
        categories = list(map(self._process_category, categories_info))

        return categories

    def _generate_dataframe(self) -> pd.DataFrame:
        print("Cleaning final data...")
        product_dfs = [
            pd.DataFrame(dataclasses.asdict(product), index=[0]).assign(
                subtype=subtype.name,
                subcategory=subcategory.name,
                category=category.name,
                vendor=self.VENDOR_NAME,
            )
            for category in self.categories
            for subcategory in category.subcategories
            for subtype in subcategory.subtypes
            for product in subtype.products
        ]
        products_df = pd.concat(product_dfs)
        products_df.drop_duplicates(inplace=True, subset=["external_id"])
        return products_df
