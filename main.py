import math
import random


class CVRPInstance:
    def __init__(
        self, name, dimension, capacity, depot, node_coords, demands, num_vehicles
    ):
        self.name = name
        self.dimension = dimension
        self.capacity = capacity
        self.depot = depot
        self.node_coords = node_coords
        self.demands = demands
        self.distances = self._calculate_distances()
        self.num_vehicles = num_vehicles  # Número de veículos lido do nome da instância

    def _calculate_distances(self):
        distances = [[0] * self.dimension for _ in range(self.dimension)]
        for i in range(1, self.dimension + 1):
            for j in range(i + 1, self.dimension + 1):
                distance = euclidean_distance(self.node_coords[i], self.node_coords[j])
                distances[i - 1][j - 1] = distance
                distances[j - 1][i - 1] = distance
        return distances

    def generate_initial_solution(self):
        # Defina um seed fixo para testes reprodutíveis (opcional):
        # random.seed(0)

        remaining_clients = set(range(1, self.dimension + 1))
        remaining_clients.remove(
            self.depot
        )  # Remove o depósito do conjunto de clientes
        solution = []

        while remaining_clients:
            # Escolhe aleatoriamente um cliente como ponto de partida desta rota
            current_node = random.choice(list(remaining_clients))
            route = [current_node]
            current_capacity = self.capacity - self.demands[current_node]
            remaining_clients.remove(current_node)

            # Expande a rota usando vizinho mais próximo até não haver mais capacidade
            while True:
                closest_client = None
                closest_distance = float("inf")

                for client in remaining_clients:
                    if self.demands[client] <= current_capacity:
                        dist = self.distances[current_node - 1][client - 1]
                        if dist < closest_distance:
                            closest_distance = dist
                            closest_client = client

                if closest_client is None:
                    # Não conseguimos adicionar mais clientes nesta rota
                    break

                route.append(closest_client)
                current_capacity -= self.demands[closest_client]
                remaining_clients.remove(closest_client)
                current_node = closest_client

            # Finaliza a rota retornando ao depósito
            solution.append([self.depot] + route + [self.depot])

        return solution


def euclidean_distance(coord1, coord2):
    return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)


def extract_num_vehicles(name):
    parts = name.split("-")
    if len(parts) > 2:
        num_vehicles = parts[-1].split("k")[-1]  # Pega o número após "k"
        return int(num_vehicles)
    raise ValueError("Número de veículos não encontrado no nome da instância")


def load_instance(file_path):
    with open(file_path, "r") as file:
        name = ""
        dimension = 0
        capacity = 0
        node_coords = {}
        demands = {}
        depot = None
        section = None

        for line in file:
            line = line.strip()
            if line.startswith("NAME"):
                name = line.split(":")[1].strip()
            elif line.startswith("DIMENSION"):
                dimension = int(line.split(":")[1].strip())
            elif line.startswith("CAPACITY"):
                capacity = int(line.split(":")[1].strip())
            elif line.startswith("NODE_COORD_SECTION"):
                section = "NODE_COORD_SECTION"
            elif line.startswith("DEMAND_SECTION"):
                section = "DEMAND_SECTION"
            elif line.startswith("DEPOT_SECTION"):
                section = "DEPOT_SECTION"
            elif line.startswith("EOF"):
                break
            elif section == "NODE_COORD_SECTION":
                parts = line.split()
                node_coords[int(parts[0])] = (int(parts[1]), int(parts[2]))
            elif section == "DEMAND_SECTION":
                parts = line.split()
                demands[int(parts[0])] = int(parts[1])
            elif section == "DEPOT_SECTION":
                depot = int(line) if line != "-1" else depot

        num_vehicles = extract_num_vehicles(name)

    return CVRPInstance(
        name, dimension, capacity, depot, node_coords, demands, num_vehicles
    )


# Exemplo de uso
if __name__ == "__main__":
    instance = load_instance("./Vrp-Set-A/A/A-n32-k5.vrp")
    initial_solution = instance.generate_initial_solution()

    print("Solução Inicial (Cliente Aleatório + Vizinho Mais Próximo):")
    for i, route in enumerate(initial_solution, start=1):
        print(f"Veículo {i}: {route}")

    print(f"Número de veículos (lido do nome): {instance.num_vehicles}")
