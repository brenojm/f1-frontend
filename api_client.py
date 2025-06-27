import requests

BASE_URL = "http://localhost:8000/api"

class ApiClient:
    def _make_request(self, method, endpoint, data=None):
        url = f"{BASE_URL}/{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, params=data)
            elif method == "POST":
                response = requests.post(url, data=data)
            elif method == "PUT":
                response = requests.put(url, data=data)
            elif method == "DELETE":
                response = requests.delete(url)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            if response.status_code == 204: # No Content for successful delete
                return True
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            return {"error": e.response.text}
        except requests.exceptions.ConnectionError as e:
            print(f"Connection Error: {e}")
            return {"error": "Could not connect to the API. Is the server running?"}
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return {"error": str(e)}

    # Drivers
    def get_drivers(self):
        return self._make_request("GET", "drivers")

    def get_driver(self, driver_id):
        return self._make_request("GET", f"drivers/{driver_id}")

    def add_driver(self, data):
        return self._make_request("POST", "drivers", data=data)

    def update_driver(self, driver_id, data):
        return self._make_request("PUT", f"drivers/{driver_id}", data=data)

    def delete_driver(self, driver_id):
        return self._make_request("DELETE", f"drivers/{driver_id}")

    # Teams
    def get_teams(self):
        return self._make_request("GET", "teams")

    def get_team(self, team_id):
        return self._make_request("GET", f"teams/{team_id}")

    def add_team(self, data):
        return self._make_request("POST", "teams", data=data)

    def update_team(self, team_id, data):
        return self._make_request("PUT", f"teams/{team_id}", data=data)

    def delete_team(self, team_id):
        return self._make_request("DELETE", f"teams/{team_id}")

    # Seasons
    def get_seasons(self):
        return self._make_request("GET", "seasons")

    def get_season(self, season_id):
        return self._make_request("GET", f"seasons/{season_id}")

    def add_season(self, data):
        return self._make_request("POST", "seasons", data=data)

    def update_season(self, season_id, data):
        return self._make_request("PUT", f"seasons/{season_id}", data=data)

    def delete_season(self, season_id):
        return self._make_request("DELETE", f"seasons/{season_id}")

    def get_driver_standings(self, season_id):
        return self._make_request("GET", f"seasons/{season_id}/standings/drivers")

    def get_team_standings(self, season_id):
        return self._make_request("GET", f"seasons/{season_id}/standings/teams")

    # Circuits
    def get_circuits(self):
        return self._make_request("GET", "circuits")

    def get_circuit(self, circuit_id):
        return self._make_request("GET", f"circuits/{circuit_id}")

    def add_circuit(self, data):
        return self._make_request("POST", "circuits", data=data)

    def update_circuit(self, circuit_id, data):
        return self._make_request("PUT", f"circuits/{circuit_id}", data=data)

    def delete_circuit(self, circuit_id):
        return self._make_request("DELETE", f"circuits/{circuit_id}")

    # Races
    def get_races(self):
        return self._make_request("GET", "races")

    def get_race(self, race_id):
        return self._make_request("GET", f"races/{race_id}")

    def add_race(self, data):
        return self._make_request("POST", "races", data=data)

    def update_race(self, race_id, data):
        return self._make_request("PUT", f"races/{race_id}", data=data)

    def delete_race(self, race_id):
        return self._make_request("DELETE", f"races/{race_id}")

    # Driver Contracts
    def get_contracts(self):
        return self._make_request("GET", "contracts")

    def get_contract(self, contract_id):
        return self._make_request("GET", f"contracts/{contract_id}")

    def add_contract(self, data):
        return self._make_request("POST", "contracts", data=data)

    def update_contract(self, contract_id, data):
        return self._make_request("PUT", f"contracts/{contract_id}", data=data)

    def delete_contract(self, contract_id):
        return self._make_request("DELETE", f"contracts/{contract_id}")

    # Results
    def get_results(self):
        return self._make_request("GET", "results")

    def get_result(self, result_id):
        return self._make_request("GET", f"results/{result_id}")

    def add_result(self, data):
        return self._make_request("POST", "results", data=data)

    def update_result(self, result_id, data):
        return self._make_request("PUT", f"results/{result_id}", data=data)

    def delete_result(self, result_id):
        return self._make_request("DELETE", f"results/{result_id}")