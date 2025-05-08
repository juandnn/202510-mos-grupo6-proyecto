import argparse
import json
import math
from typing import Dict

import pandas as pd
import requests
from geopy.distance import geodesic


class SolutionValidator:
    def __init__(
        self,
        distance_method: str = "haversine",
        cache_file: str = "distance_cache.json",
    ):
        self.distance_method = distance_method
        self.cache_file = cache_file
        self.distance_cache = {}
        self.load_cache()

        try:
            # Load data
            self.vehicles_df = pd.read_csv("datos/caso_1/vehicles.csv")
            self.clients_df = pd.read_csv("datos/caso_1/clients.csv")
            self.depots_df = pd.read_csv("datos/caso_1/depots.csv")
            self.solution_df = pd.read_csv("solution.csv")

            # Create coordinate mappings
            self.locations = {}

            # Map depots with their alphanumeric identifiers
            # Based on your data, depot 1 maps to "CDA"
            for _, depot in self.depots_df.iterrows():
                depot_numeric_id = int(depot["DepotID"])

                # Map numeric ID
                self.locations[depot_numeric_id] = {
                    "latitude": depot["Latitude"],
                    "longitude": depot["Longitude"],
                    "type": "depot",
                }

                # Map alphanumeric ID (CDA for depot 1)
                if depot_numeric_id == 1:
                    self.locations["CDA"] = {
                        "latitude": depot["Latitude"],
                        "longitude": depot["Longitude"],
                        "type": "depot",
                    }

            # Add client coordinates
            for _, client in self.clients_df.iterrows():
                client_id = f"C{int(client['ClientID']):03d}"
                self.locations[client_id] = {
                    "latitude": client["Latitude"],
                    "longitude": client["Longitude"],
                    "type": "client",
                    "demand": int(client["Demand"]),
                }

            # Create lookup dictionaries
            self.client_demands = {
                f"C{int(row.ClientID):03d}": int(row.Demand)
                for _, row in self.clients_df.iterrows()
            }

            self.vehicle_specs = {
                int(row.VehicleID): {
                    "capacity": int(row.Capacity),
                    "range": int(row.Range),
                }
                for _, row in self.vehicles_df.iterrows()
            }

        except Exception as e:
            print(f"Error during initialization: {str(e)}")
            raise

    def load_cache(self):
        """Load distance cache from file."""
        try:
            with open(self.cache_file, "r") as f:
                self.distance_cache = json.load(f)
        except FileNotFoundError:
            self.distance_cache = {}

    def save_cache(self):
        """Save distance cache to file."""
        with open(self.cache_file, "w") as f:
            json.dump(self.distance_cache, f)

    def haversine_distance(self, loc1: str, loc2: str) -> float:
        """Calculate the distance between two locations using Haversine formula."""
        p1 = self.locations[loc1]
        p2 = self.locations[loc2]

        lat1, lon1 = p1["latitude"], p1["longitude"]
        lat2, lon2 = p2["latitude"], p2["longitude"]

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        earth_radius = 6371

        return earth_radius * c

    def geopy_distance(self, loc1: str, loc2: str) -> float:
        """Calculate distance using GeoPy."""
        p1 = self.locations[loc1]
        p2 = self.locations[loc2]

        coord1 = (p1["latitude"], p1["longitude"])
        coord2 = (p2["latitude"], p2["longitude"])

        return geodesic(coord1, coord2).kilometers

    def osrm_distance(self, loc1: str, loc2: str) -> float:
        """Calculate distance using OSRM API."""
        p1 = self.locations[loc1]
        p2 = self.locations[loc2]

        url = f"http://router.project-osrm.org/route/v1/driving/{p1['longitude']},{p1['latitude']};{p2['longitude']},{p2['latitude']}"

        try:
            response = requests.get(url)
            data = response.json()

            if "routes" in data and len(data["routes"]) > 0:
                # Distance in meters, convert to kilometers
                return data["routes"][0]["distance"] / 1000
            else:
                print(
                    f"OSRM API failed for {loc1} to {loc2}, falling back to Haversine"
                )
                return self.haversine_distance(loc1, loc2)
        except Exception as e:
            print(f"Error with OSRM API: {e}, falling back to Haversine")
            return self.haversine_distance(loc1, loc2)

    def calculate_distance(self, loc1: str, loc2: str) -> float:
        """Calculate distance using the selected method with caching."""
        cache_key = f"{loc1}_{loc2}_{self.distance_method}"

        # Check cache first
        if cache_key in self.distance_cache:
            return self.distance_cache[cache_key]

        # Calculate distance based on method
        if self.distance_method == "haversine":
            distance = self.haversine_distance(loc1, loc2)
        elif self.distance_method == "geopy":
            distance = self.geopy_distance(loc1, loc2)
        elif self.distance_method == "osrm":
            distance = self.osrm_distance(loc1, loc2)
        else:
            raise ValueError(f"Unknown distance method: {self.distance_method}")

        # Cache the result
        self.distance_cache[cache_key] = distance

        return distance

    def validate_solution(self) -> Dict:
        """Validate the solution according to the specified requirements."""
        errors = []
        visited_clients = set()

        for idx, route in self.solution_df.iterrows():
            vehicle_id = route["VehicleId"]
            depot_id = route["DepotId"]
            initial_load = int(route["InitialLoad"])
            route_sequence = route["RouteSequence"].split("-")
            clients_served = int(route["ClientsServed"])
            demands_satisfied = [int(d) for d in route["DemandsSatisfied"].split("-")]

            vehicle_number = int(vehicle_id.replace("VEH", ""))
            vehicle_spec = self.vehicle_specs[vehicle_number]

            # Check 1: Route starts and ends at depot
            if route_sequence[0] != depot_id or route_sequence[-1] != depot_id:
                errors.append(
                    f"Route {vehicle_id} does not start and end at depot {depot_id}"
                )

            # Check 2: Vehicle capacity
            if initial_load > vehicle_spec["capacity"]:
                errors.append(
                    f"Route {vehicle_id} exceeds capacity: {initial_load} > {vehicle_spec['capacity']}"
                )

            # Check 3: Route range
            total_distance = 0
            for i in range(len(route_sequence) - 1):
                from_loc = route_sequence[i]
                to_loc = route_sequence[i + 1]

                # Check if locations exist before calculating distance
                if from_loc not in self.locations:
                    errors.append(
                        f"Route {vehicle_id} has invalid location: {from_loc}"
                    )
                    continue
                if to_loc not in self.locations:
                    errors.append(f"Route {vehicle_id} has invalid location: {to_loc}")
                    continue

                try:
                    distance = self.calculate_distance(from_loc, to_loc)
                    total_distance += distance
                except Exception as e:
                    errors.append(
                        f"Route {vehicle_id} distance calculation error: {str(e)}"
                    )

            if total_distance > vehicle_spec["range"]:
                errors.append(
                    f"Route {vehicle_id} exceeds range: {total_distance:.1f} > {vehicle_spec['range']}"
                )

            # Check 4: Track visited clients and demand satisfaction
            client_idx = 0
            for i, loc in enumerate(route_sequence):
                # Only count locations that start with C and are actual clients (not depots)
                if loc.startswith("C") and loc not in ["CDA", "CDB", "CDC"]:
                    if client_idx >= len(demands_satisfied):
                        errors.append(
                            f"Route {vehicle_id} has missing demand value for client {loc}"
                        )
                        continue

                    visited_clients.add(loc)
                    expected_demand = self.client_demands.get(loc, 0)
                    actual_demand = demands_satisfied[client_idx]

                    if actual_demand != expected_demand:
                        errors.append(
                            f"Route {vehicle_id} has incorrect demand for {loc}: {actual_demand} != {expected_demand}"
                        )

                    client_idx += 1

            # Check for duplicate client visits
            route_clients = [
                loc
                for loc in route_sequence
                if loc.startswith("C") and loc not in ["CDA", "CDB", "CDC"]
            ]
            if len(route_clients) != len(set(route_clients)):
                errors.append(f"Route {vehicle_id} has duplicate client visits")

            # Verify clients_served count
            if len(route_clients) != clients_served:
                errors.append(
                    f"Route {vehicle_id} clients_served mismatch: {len(route_clients)} != {clients_served}"
                )

        # Check 5: All clients visited
        all_clients = set(self.client_demands.keys())
        missing_clients = all_clients - visited_clients
        if missing_clients:
            for client in missing_clients:
                errors.append(f"Client {client} was not visited")

        # Save cache before returning
        self.save_cache()

        return {"feasible": len(errors) == 0, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description="Vehicle Routing Solution Validator")
    parser.add_argument(
        "--method",
        type=str,
        choices=["haversine", "geopy", "osrm"],
        default="haversine",
        help="Distance calculation method",
    )
    parser.add_argument(
        "--cache", type=str, default="distance_cache.json", help="Path to cache file"
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    try:
        print(
            f"Starting solution validation with {args.method} distance calculation..."
        )
        print("Note: TotalDistance, TotalTime, and FuelCost columns are ignored\n")

        validator = SolutionValidator(
            distance_method=args.method, cache_file=args.cache
        )
        result = validator.validate_solution()

        if result["feasible"]:
            print("SOLUTION IS FEASIBLE!")
            print("All routes satisfy the requirements.")
        else:
            print("SOLUTION IS INFEASIBLE!")
            print("Errors found:")
            for error in result["errors"]:
                print(f"- {error}")

        if args.verbose:
            print("\nValidation completed successfully!")

    except Exception as e:
        print(f"Error during validation: {str(e)}")


if __name__ == "__main__":
    main()