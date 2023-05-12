"""
This module is used to generate our dummy data for the VeloSimulator™
"""
import json

def process_velo_dataset(input_dir:str,output_dir:str):
    """
    This function gets the original velo json file and removes unused data
    """
    with open(f"{input_dir}/velo.json", "r", encoding="UTF-8") as file:
        data = json.load(file)
        new_data = {"type": "FeatureCollection", "name": "velo", "features": []}
        index = 0
        for feature in data["features"]:
            new_feature = {
                "Index": index,
                "Properties": {
                    "Naam": feature["properties"]["Naam"],
                    "Straatnaam": feature["properties"]["Straatnaam"],
                    "Huisnummer": feature["properties"]["Huisnummer"],
                    "District": feature["properties"]["District"],
                    "Postcode": feature["properties"]["Postcode"],
                    "Stationnummer": feature["properties"]["Objectcode"][3:],
                    "Aantalplaatsen": feature["properties"]["Aantal_plaatsen"],
                    "Gebruik":feature["properties"]["Gebruik"]
                },
                "Geometry": feature["geometry"],
            }
            if new_feature["Properties"]["Gebruik"] == "IN_GEBRUIK":
                new_data["features"].append(new_feature)
                index += 1
    with open(f"{output_dir}/velo.json", "w", encoding="UTF-8") as newjson:
        json.dump(new_data, newjson, indent=6)

#process_velo_dataset("input","libs").

def create_users(input_dir:str,output_dir:str):
    """
    This function creates 
    """
    with open(f"{input_dir}/users.json", "r", encoding="UTF-8") as file:
        data = json.load(file)

