"""
Dit is een simulator voor 
het leenfietsen project van 
de stad Antwerpen.
"""
import pickle
import json
import sys
import os
import re
import time
import datetime
from jinja2 import Environment, FileSystemLoader
import yaml
import numpy as np


class MissingJsonFilesError(Exception):
    """
    A custom error to let the user know what went wrong
    """

    def __init__(self, missing_files):
        self.missing_files = missing_files
        print(
            "De volgende .JSON files die nodig"
            + " zijn voor het setup process missen in de"
            + f" input directory: {', '.join(self.missing_files)}"
        )
        exit(2)


class LogSizeOverflow(Exception):
    """
    A custom error to let the user know what went wrong
    """

    def __init__(self, string: str) -> None:
        print(string)
        exit(1)


class Fiets:
    """
    Deze class representeert een fiets

    Class attributen:
        - aantal_fietsen [int]
        - max_fietsen [int]

    Instance attrbuten:
        - _laatste_gebruiker [Gebruiker]
        - _nummer [int]
    """

    aantal_fietsen = 0
    max_fietsen = 0

    def __init__(self):
        self._nummer = Fiets.aantal_fietsen
        Fiets.aantal_fietsen += 1

    def getter(self) -> dict:
        """
        Returns certain attributes in a dictionary
        """
        attributes = {"nummer": self._nummer}
        return attributes


class Slot:
    """
    Deze class representeert een slot in een station

    Instance attrbuten:
        - _bezet [Bool]
        - _fiets [Fiets]
    """

    def __init__(self):
        self.leeg = True
        self._fiets = None

    def fiets_deponeren(self, fiets: Fiets):
        """
        Je zet een fiets in het slot
        """
        if not self.leeg:
            raise ValueError
        if self.leeg:
            self.leeg = False
        self._fiets = fiets

    def fiets_pakken(self):
        """
        Je haalt een fiets uit een slot
        """
        fiets = self._fiets
        self._fiets = None
        self.leeg = True
        return fiets


class Station:
    """
    Deze class representeert een station

    Instance attrbuten:
        - stationnummer [int]
        - aantal_slots [int]
        - vol [bool]
        - slots [Slot]
        - adres [dict[str]]
        - coordinaten [dict[float]]
    """

    def __init__(
        self, stationnummer: int, adres: dict, coordinaten: dict, aantal_slots: int
    ) -> None:
        self._stationnummer = stationnummer
        self.aantal_slots = aantal_slots
        self.vol = False
        self.leeg = True
        self._slots = []
        self.aantal_vol = 0
        while len(self._slots) < self.aantal_slots:
            slot = Slot()
            self._slots.append(slot)
        self._adres = adres
        self._coordinaten = coordinaten

    def voeg_fiets_toe(self, fiets: Fiets):
        """
        Voeg een fiets toe aan een station
        """
        for slot in self._slots:
            if slot.leeg:
                self.aantal_vol += 1
                slot.fiets_deponeren(fiets)
                self.leeg = False
                break

            if self.aantal_vol == self.aantal_slots:
                self.vol = True

    def neem_fiets(self):
        """
        Neem een fiets van het station
        """
        for slot in self._slots:
            if self.aantal_vol == 0:
                self.leeg = True
                self.vol = False

            if not slot.leeg:
                self.aantal_vol -= 1
                return slot.fiets_pakken()

    def getter(self) -> dict:
        """
        Returns certain attributes in a dictionary
        """
        attributes = {"nummer": self._stationnummer, "adres": self._adres}
        return attributes


class Rit:
    """
    Deze class representeert een rit vanself._gebruiker
    station A -> Station B met Fiets x

    Deze klasse werkt als een log

    Instance attrbuten:
        - startstation [Station]
        - eindstation [Station]
        - fiets [Fiets]
        - afstand [float] (km)
        - geschatte_tijd [float] (min)
    """

    def __init__(
        self, startstation: Station, eindstation: Station, fiets: Fiets, uitvoerder
    ) -> None:
        self._uitvoerder = uitvoerder
        self._uitvoerder._verplaatsings_update()
        self._fiets = fiets
        self._startstation = startstation
        self._eindstation = eindstation

        self._afstand = self.__calculate_distance(
            startstation._coordinaten["Y"],
            startstation._coordinaten["X"],
            eindstation._coordinaten["Y"],
            eindstation._coordinaten["X"],
        )
        self._geschatte_tijd = self.__calculate_estimate_time(self._afstand)

    def __calculate_distance(
        self, x_a: float, y_a: float, x_b: float, y_b: float
    ) -> float:
        lat1, lat2 = np.radians(x_a), np.radians(x_b)
        lon1, lon2 = np.radians(y_a), np.radians(y_b)
        coords1 = np.vstack((lat1, lon1)).T
        coords2 = np.vstack((lat2, lon2)).T
        d_coords = coords2 - coords1
        sqr_half = (
            np.sin(d_coords[:, 0] / 2) ** 2
            + np.cos(coords1[:, 0])
            * np.cos(coords2[:, 0])
            * np.sin(d_coords[:, 1] / 2) ** 2
        )
        cent_angle = 2 * np.arctan2(np.sqrt(sqr_half), np.sqrt(1 - sqr_half))
        distance = 6371 * cent_angle
        return distance[0]

    def __calculate_estimate_time(self, distance_km: float):
        average_speed = 16
        time_hours = distance_km / average_speed
        time_minutes = time_hours * 60
        return time_minutes

    def getter(self) -> dict:
        """
        Returns certain attributes in a dictionary
        """
        tijd = datetime.datetime.fromtimestamp(time.time()).strftime(
            "%H:%M:%S"
        )
        gebruiker_info = self._uitvoerder.getter()

        fiets_info = self._fiets.getter()

        start_station_info = self._startstation.getter()
        eind_station_info = self._eindstation.getter()

        afstand = self._afstand
        geschatte_tijd = self._geschatte_tijd

        attributes = {
            "time": tijd,
            "gebruiker": gebruiker_info,
            "fiets": fiets_info,
            "start_station": start_station_info,
            "eind_station": eind_station_info,
            "afstand": round(afstand,2),
            "geschatte_tijd": round(geschatte_tijd,2),
        }
        return attributes


class Gebruiker:
    """
    Deze class representeert een gebruiker

    Class attributen:
        - aantal_gebruikers [int]
        - max_gebruikers [int]

    Instance attrbuten:
        - _sex [str] (2 options)
        - _voornaam [str]
        - _achternaam [str]
        - _aantal_ritten [int]
        - _laatste_rit [Rit]
    """

    aantal_gebruikers = 0
    max_gebruikers = 0

    def __init__(self, voornaam_man: list, voornaam_vrouw: list, achternaam: list):
        self._voornaam = (
            voornaam_man[np.random.randint(0, len(voornaam_man))]
            if np.random.randint(0, 2) > 0.5
            else voornaam_vrouw[np.random.randint(0, len(voornaam_vrouw))]
        )
        self._achternaam = achternaam[np.random.randint(0, len(achternaam))]
        self._aantal_ritten = 0
        self._nummer = Gebruiker.aantal_gebruikers
        Gebruiker.aantal_gebruikers += 1

    def _verplaatsings_update(self):
        """
        Deze functie update een aantal instance attributen
        """
        self._aantal_ritten += 1

    def getter(self) -> dict:
        """
        Returns certain attributes in a dictionary
        """
        attributes = {
            "type": "Gebruiker",
            "nummer": self._nummer,
            "voornaam": self._voornaam,
            "achternaam": self._achternaam,
            "aantal_ritten": self._aantal_ritten,
        }
        return attributes


class Fietstransporteur:
    """
    Deze class representeert een fietstransporteur
    """

    aantal_transporteurs = 0
    max_transporteurs = 0

    def __init__(self):
        self._aantal_ritten = 0
        self._nummer = Fietstransporteur.aantal_transporteurs
        Fietstransporteur.aantal_transporteurs += 1

    def _verplaatsings_update(self):
        """
        Deze functie update een aantal instance attributen
        """
        self._aantal_ritten += 1

    def __str__(self) -> str:
        return f"{self._nummer}"

    def getter(self) -> dict:
        """
        Returns certain attributes in a dictionary
        """
        attributes = {
            "type": "Transporteur",
            "nummer": self._nummer,
            "aantal_ritten": self._aantal_ritten / 10,
        }
        return attributes


class Log:
    """
    Writes different events in a log file
    """

    max_total_log_size = 0

    def __init__(self):
        self.ritlogfile = "output/ritlog.json"
        if not os.path.exists(self.ritlogfile):
            with open(self.ritlogfile, "w", encoding="UTF-8") as file:
                json.dump([], file)

    def __calculate_file_size(self):
        """
        Calculates the total file size of the log files
        """
        file_paths = [self.ritlogfile]
        total_size = 0

        for file_path in file_paths:
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)

        if total_size >= Log.max_total_log_size:
            raise LogSizeOverflow("Log files have exceeded config limit.")

    def __load_log_data(self) -> list:
        """
        Loads existing log data from a file.
        """
        try:
            with open(self.ritlogfile, "r", encoding="UTF-8") as file:
                logs = json.load(file)
        except FileNotFoundError:
            logs = []
        return logs

    def log_rit(self, cycle: int, ritten: list):
        """
        Writes a rit into the log.
        """
        logs = self.__load_log_data()
        ritten_info = []
        for rit in ritten:
            ritten_info.append(rit.getter())
        logs.append({"cycle": cycle, "events": ritten_info})

        with open(self.ritlogfile, "w", encoding="UTF-8") as file:
            json.dump(logs, file,indent=6)

        self.__calculate_file_size()
        time.sleep(5)


class WebsiteMaker:
    """
    Creates a static html page
    """

    def __init__(self):
        self._json_file_path = "output/ritlog.json"
        self._template_file_path = "input/viewer.html"
        self._output_file_path = "site/index.html"

    def generate_html(self):
        """
        Generates a static html page
        """
        with open(self._json_file_path, "r", encoding="UTF-8") as json_file:
            log_data = json.load(json_file)

        env = Environment(loader=FileSystemLoader("."))
        template = env.get_template(self._template_file_path)

        rendered_html = template.render(data=log_data)

        with open(self._output_file_path, "w", encoding="UTF-8") as output_file:
            output_file.write(rendered_html)


class App:
    """
    Deze class representeert onze simulator app
    Deze wordt gebruikt om alle onderliggende code
    te besturen.
    """

    def __init__(self):
        self._cycle = 0
        self._ritten = []
        self._stations = []
        self._gebruikers = []
        self._fietsen = []
        self._transporteurs = []
        self._willekeurigheid = 0
        self._tijd_verhouding = 0

    def setup(self) -> None:
        """
        Runs the program setup process:

        Step 1
            -> check if all directories are available
                - input,config,output
            -> create missing directories if needed
        step 2
            -> check if all files are in each directory
                - config: config.yaml
                - input: names.json, velo.json if missing send error
            -> load and assign config parameters
            -> create app.pickle
        """

        # region stap1
        dirs_needed = ["input", "config", "output", "site"]
        dirs_present = self._check_dir("input", "config", "output", "site")
        dirs_to_create = self._mask_list(dirs_needed, dirs_present)
        self._make_dir(*dirs_to_create)

        if "input" in dirs_to_create and "output" in dirs_to_create:
            missing_files = ["names.json", "velo.json", "viewer.html"]
            raise MissingJsonFilesError(missing_files)
        # endregion

        # region stap2
        config_file_present = self._check_files("config", "config.yaml")
        if config_file_present[0] is False:
            self._create_config()
        self._load_config()
        self._create_users()
        self._create_bikemovers()
        self._create_bikes()
        self._create_stations()
        self._populate_stations()
        # endregion

    def run(self) -> None:
        """
        runs the simulation
        """
        print("To quit press ctrl + c")
        self._load_config()
        while True:
            print(f'running cycle-{self._cycle}')
            # two ways to break this loop
            # (1) ctrl+c
            # (2) log size too large
            try:
                amount_of_rides = self.__random_rit_amount()
                for _ in range(0, amount_of_rides):
                    self.__user_cycle()
                full_stations = [
                    station
                    for station in self._stations
                    if station.aantal_vol == station.aantal_slots
                ]
                if len(full_stations) > 20:
                    self.__transporter_cycle()
                self.__log()
                # for rit in self._ritten:
                #     print(rit.getter())
                # input()
            except KeyboardInterrupt:
                break

    def view(self):
        """
        Built-in log file viewer
        """
        velosim_website = WebsiteMaker()
        velosim_website.generate_html()

    # region __functions-setup__
    def _check_dir(self, *dir_names: str) -> list[bool]:
        """
        Checks if a given directory exists

        Attributes:
            dir_names [str] -> name of dir / path (allows multi input)

        Output:
            exists? `True` / `False` (1 dirname given)/n
            exists? [`True` / `False`, `...`] (1+ dirname given)
        """
        res = []
        for dir_name in dir_names:
            if os.path.exists(dir_name) and os.path.isdir(dir_name):
                res.append(True)
            else:
                res.append(False)
        return res

    def _make_dir(self, *dir_names: str) -> None:
        """
        Creates a given dir

        Attributes:
            dir_name [str] -> names of dir / path (allows multi input)

        Output:
            /
        """
        for dir_name in dir_names:
            os.makedirs(dir_name)

    def _mask_list(self, original_list: list[str], mask: list[bool]) -> list[str]:
        masked_list = []
        for item, mask in zip(original_list, mask):
            if not mask:
                masked_list.append(item)
        return masked_list

    def _check_files(self, directory: str, *files: list) -> list[bool]:
        """
        Checks the input directory to see if specified files exist,
        returns a list of true and false values
        """
        existing_files = []
        for file in files:
            try:
                with open(
                    f"{directory}/{file}",
                    "r",
                    encoding="UTF-8",
                ):
                    existing_files.append(True)
            except FileNotFoundError:
                existing_files.append(False)
        return existing_files

    def _create_stations(self) -> None:
        """
        This function removes unused data
        from the velo.json file
        and puts the stations in self._stations
        """
        with open("input/velo.json", "r", encoding="UTF-8") as file:
            data = json.load(file)
            for feature in data["features"]:
                if feature["properties"]["Gebruik"] == "IN_GEBRUIK":
                    stationsnummer = feature["properties"]["Objectcode"][3:]
                    adres = {
                        "Straatnaam": feature["properties"]["Straatnaam"],
                        "Huisnummer": feature["properties"]["Huisnummer"],
                        "Gemeente": feature["properties"]["District"],
                        "Postcode": feature["properties"]["Postcode"],
                    }
                    coordinaten = {
                        "X": float(feature["geometry"]["coordinates"][0]),
                        "Y": float(feature["geometry"]["coordinates"][1]),
                    }
                    aantal_slots = int(feature["properties"]["Aantal_plaatsen"])

                    station = Station(stationsnummer, adres, coordinaten, aantal_slots)
                    self._stations.append(station)
                else:
                    continue

    def _create_users(self) -> None:
        """
        This function creates a number of 'users'
        specified by the amount in the config file.
        And puts them in self._gebruikers
        """
        with open(r"input/names.json", "r", encoding="UTF-8") as file:
            data = json.load(file)
            voornaam_man = data["Mannen_Voornaam"]
            voornaam_vrouw = data["Vrouwen_Voornaam"]
            achternaam = data["Achternaam"]

            while Gebruiker.aantal_gebruikers < Gebruiker.max_gebruikers:
                gebruiker = Gebruiker(voornaam_man, voornaam_vrouw, achternaam)
                self._gebruikers.append(gebruiker)

    def _create_bikes(self) -> None:
        """
        This function creates a number of 'bikes' specified
        by the amount in the config file. And puts them in
        self._fietsen
        """
        while Fiets.aantal_fietsen < Fiets.max_fietsen:
            fiets = Fiets()
            self._fietsen.append(fiets)

    def _create_bikemovers(self) -> None:
        """
        This function creates a number of 'bikemovers' specified
        by the amount in the config file. And puts them in
        self._transporteurs
        """
        while (
            Fietstransporteur.aantal_transporteurs < Fietstransporteur.max_transporteurs
        ):
            fietstransporteur = Fietstransporteur()
            self._transporteurs.append(fietstransporteur)

    def _populate_stations(self):
        # there's a bug here,
        # i tried to remove it but
        # it is stubborn
        #
        # too bad! :(
        indexen = list(range(len(self._stations)))
        for fiets in self._fietsen:
            index = np.random.choice(indexen)
            while self._stations[index].vol:
                indexen.remove(index)
                index = np.random.choice(indexen)
            station = self._stations[index]
            station.voeg_fiets_toe(fiets)

    def _create_config(self) -> None:
        file_path = os.path.join("config", "config.yaml")
        config_data = {
            "max_log_bestandsgrote": 10,
            "aantal_gebruikers": 100,
            "aantal_fietsen": 50,
            "aantal_transporteurs": 25,
            "willekeurigheid": 50,
            "tijd_verhouding": 30,
        }
        with open(file_path, "w", encoding="UTF-8") as config_file:
            yaml.dump(config_data, config_file)
            config_file.write(
                "# max aantal fietsen 9627\n"
                + "# max log bestands grote in megabytes\n"
                + "# willekeurigheids percentage (tussen 0-100)\n"
                + "# tijd verhouding 1 cycle = x min in simulatie\n"
                + "    # Hogere random ~ meer ritten\n"
                + "    # Hogere tijd verhouding ~ meer ritten"
            )

    def _load_config(self) -> None:
        with open("config/config.yaml", "r", encoding="UTF-8") as config_file:
            config_data = yaml.safe_load(config_file)
            Gebruiker.max_gebruikers = config_data["aantal_gebruikers"]
            Fiets.max_fietsen = config_data["aantal_fietsen"]
            Fietstransporteur.max_transporteurs = config_data["aantal_transporteurs"]
            self._willekeurigheid = config_data["willekeurigheid"]
            self._tijd_verhouding = config_data["tijd_verhouding"]
            Log.max_total_log_size = config_data["max_log_bestandsgrote"] * 1024 * 1024

    # endregion

    # region __functions_run_
    def __log(self) -> None:
        log = Log()
        log.log_rit(self._cycle, self._ritten)
        self._cycle += 1
        self._ritten.clear()

    def __random_rit_amount(self) -> int:
        max_range = round((self._willekeurigheid / 100) * (self._tijd_verhouding * 2))
        randomized_value = np.random.randint(1, max_range + 2)
        return int(randomized_value)

    def __user_cycle(self) -> None:
        gebruiker = np.random.choice(self._gebruikers)

        non_empty_stations = [
            station for station in self._stations if station.aantal_vol > 0
        ]
        non_full_stations = [
            station
            for station in self._stations
            if station.aantal_vol < station.aantal_slots
        ]

        start_station = np.random.choice(non_empty_stations)
        if start_station in non_full_stations:
            non_full_stations.remove(start_station)
        end_station = np.random.choice(non_full_stations)

        bike = start_station.neem_fiets()
        end_station.voeg_fiets_toe(bike)

        rit = Rit(start_station, end_station, bike, gebruiker)
        self._ritten.append(rit)

    def __transporter_cycle(self) -> None:
        full_stations = [
            station
            for station in self._stations
            if station.aantal_slots >= 22 and station.aantal_vol >= 20
        ]
        empty_stations = [
            station for station in self._stations if station.aantal_vol - 22 >= 0
        ]
        for _ in range(np.random.randint(0, 11)):
            if len(empty_stations) <= 0 or len(full_stations) <= 0:
                break
            start_station = np.random.choice(full_stations)
            end_station = np.random.choice(empty_stations)
            driver = np.random.choice(self._transporteurs)
            for _ in range(10):
                bike = start_station.neem_fiets()
                if start_station.aantal_vol <= 0:
                    break
                rit = Rit(start_station, end_station, bike, driver)
                end_station.voeg_fiets_toe(bike)
                self._ritten.append(rit)
            empty_stations.remove(end_station)
            full_stations.remove(start_station)

    # endregion


def main():
    """
    Processes sys.argv flags, and
    runs the according functions
    """
    # region patterns
    setup_pat = r"^(-{1,2}[sS]|-{1,2}[sS]etup)$"
    run_pat = r"^(-{1,2}[rR]|-{1,2}[rR]un)$"
    view_pat = r"^(-{1,2}[vV]|-{1,2}[vV]iew)$"
    # endregion
    if len(sys.argv) > 1:
        user_flag = str(sys.argv[1])

        if re.match(setup_pat, user_flag):
            velosim = App()
            velosim.setup()
            with open("output/app.pickle", "wb") as file:
                pickle.dump(velosim, file)

        elif re.match(run_pat, user_flag):
            velosim = None
            with open("output/app.pickle", "rb") as file:
                velosim = pickle.load(file)
            velosim.run()
            with open("output/app.pickle", "wb") as file:
                pickle.dump(velosim, file)

        elif re.match(view_pat, user_flag):            
            velosim = None
            with open("output/app.pickle", "rb") as file:
                velosim = pickle.load(file)
            velosim.view()
        else:
            print("Flag not recognized.")

    else:
        print("Please add a flag")


if __name__ == "__main__":
    # tic = time.time_ns()
    main()
    # toc = time.time_ns()
    # elapsed_time = toc - tic
    # print(elapsed_time)
