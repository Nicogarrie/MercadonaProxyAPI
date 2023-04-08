import dataclasses
import re
from http import client as http_client

import pandas as pd
import requests

from api_dataclasses import Category, Department, Product, Subcategory, Subtype

CSV_FILEPATH = "final_consum_products.csv"
GET_PRODUCTS_TO_CSV = True


class InvalidStatusCode(Exception):
    """
    Raised when the response code was not expected
    """


class ConsumAPI:
    VENDOR_NAME = "Consum"
    BASE_URL = "https://tienda.consum.es/api/rest/V1.0"

    def __init__(self) -> None:
        self.departments: list[Department] = list()
        self.categories: list[Category] = list()
        self.subcategories: list[Subcategory] = list()
        self.subtypes: list[Subtype] = list()
        self.products: list[Product] = list()

    @classmethod
    def export_products_to_csv(cls, file_url: str) -> None:
        api = cls()
        api._get_departments()
        products_df = api._generate_dataframe()

        print("Exporting to csv...")
        products_df.to_csv(file_url, index=False)

    def get(
        self,
        url: str,
        params: dict | None = None,
        valid_status_codes: tuple[int, ...] = (http_client.OK,),
    ) -> dict:
        params = params if params else dict()
        request_url = f"{self.BASE_URL}/{url}/"

        request = requests.get(request_url, params=params)
        if request.status_code not in valid_status_codes:
            print("Maximum request limit reached! Please wait a couple seconds.")
            raise InvalidStatusCode(f"Unexpected status code {request.status_code}")

        return request.json()

    def _process_product(self, product_info: dict) -> Product:
        external_id = product_info["id"]

        product_data = product_info["productData"]
        name = product_data["name"]
        brand = product_data["brand"]["name"]
        image_url = product_data["imageURL"]
        is_pack = False
        total_units = None
        cleaned_description = (
            product_data["description"].replace(name, "").replace(" ", "")
        )
        if cleaned_description:
            if "x" in cleaned_description:
                is_pack = True
                total_units, cleaned_description = cleaned_description.split("x")
            regex = r"\d+"
            if "," in cleaned_description:
                cleaned_description = cleaned_description.replace(",", ".")
                regex = r"\d+\.\d+"
            size = re.findall(regex, cleaned_description)[0]
            size_format = cleaned_description.replace(size, "").strip()
        else:
            size, size_format = None, None

        is_approx_size = not bool(product_data.get("format"))

        price_data = product_info["priceData"]
        price = price_data["prices"][0]["value"]["centAmount"]
        price_per_size = price_data["prices"][0]["value"]["centUnitAmount"]

        product = Product(
            external_id=external_id,
            name=name,
            brand=brand,
            image_url=image_url,
            size=float(size) if size else size,
            is_approx_size=bool(is_approx_size),
            total_units=int(total_units) if total_units else total_units,
            size_format=size_format,
            price=float(price),
            price_per_size=float(price_per_size),
            is_pack=is_pack,
        )
        self.products.append(product)

        return product

    def _get_products(self, subtype_id) -> list[Product]:
        params = {
            "limit": 999999,
            "offset": 0,
            "orderById": 7,
            "showRecommendations": False,
            "categories": subtype_id,
        }
        products_info = self.get("catalog/product", params=params)["products"]
        products = list(map(self._process_product, products_info))

        return products

    def _process_subtype(self, subtype_info: dict) -> Subtype:
        external_id = subtype_info["id"]
        name = subtype_info["nombre"]

        print(f"Getting products for {name}...")
        products = self._get_products(external_id)

        subtype = Subtype(external_id=external_id, name=name, products=products)
        self.subtypes.append(subtype)

        return subtype

    def _process_subcategory(self, subcategory_info: dict) -> Subcategory:
        external_id = subcategory_info["id"]
        name = subcategory_info["nombre"]

        print(f"Getting subtypes for {name}...")
        subtypes_info = subcategory_info["subcategories"]
        subtypes = list(map(self._process_subtype, subtypes_info))

        subcategory = Subcategory(external_id=external_id, name=name, subtypes=subtypes)
        self.subcategories.append(subcategory)

        return subcategory

    def _process_category(self, category_info: dict) -> Category:
        external_id = category_info["id"]
        name = category_info["nombre"]

        print(f"Getting subcategories for {name}...")
        subcategories_info = category_info["subcategories"]
        subcategories = list(map(self._process_subcategory, subcategories_info))

        category = Category(
            external_id=external_id, name=name, subcategories=subcategories
        )
        self.categories.append(category)

        return category

    def _process_department(self, department_info: dict) -> Department:
        external_id = department_info["id"]
        name = department_info["nombre"]

        print(f"Getting categories for {name}...")
        categories_info = department_info["subcategories"]
        categories = list(map(self._process_category, categories_info))

        department = Department(
            external_id=external_id, name=name, categories=categories
        )
        self.departments.append(department)

        return department

    def _get_departments(self) -> list[Department]:
        print("Getting departments...")
        departments_info = self.get("shopping/category/menu")
        departments = list(map(self._process_department, departments_info))

        return departments

    def _generate_dataframe(self) -> pd.DataFrame:
        print("Cleaning final data...")
        product_dfs = [
            pd.DataFrame(dataclasses.asdict(product), index=[0]).assign(
                subtype=subtype.name,
                subcategory=subcategory.name,
                category=category.name,
                department=department.name,
                vendor=self.VENDOR_NAME,
            )
            for department in self.departments
            for category in department.categories
            for subcategory in category.subcategories
            for subtype in subcategory.subtypes
            for product in subtype.products
        ]
        products_df = pd.concat(product_dfs)
        products_df.drop_duplicates(inplace=True, subset=["external_id"])
        return products_df
