import consum
import database
import mercadona
import tables

if __name__ == "__main__":
    print("Starting Mercadona products processing...")
    #
    # if mercadona.GET_PRODUCTS_TO_CSV:
    #     mercadona.MercadonaAPI.export_products_to_csv(mercadona.CSV_FILEPATH)
    # database.save_csv_in_database(tables.PRODUCTS_TABLE, mercadona.CSV_FILEPATH)
    consum.ConsumAPI.export_products_to_csv(consum.CSV_FILEPATH)
    database.save_csv_in_database(tables.PRODUCTS_TABLE, consum.CSV_FILEPATH)
    print("Process finalized successfully!")
