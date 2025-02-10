import math
import random
import copy


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
        self.num_vehicles = num_vehicles

    def _calculate_distances(self):
        distances = [[0] * self.dimension for _ in range(self.dimension)]
        for i in range(1, self.dimension + 1):
            for j in range(i + 1, self.dimension + 1):
                distance = euclidean_distance(self.node_coords[i], self.node_coords[j])
                distances[i - 1][j - 1] = distance
                distances[j - 1][i - 1] = distance
        return distances

    def generate_initial_solution(self):
        # Gera a solução inicial escolhendo aleatoriamente o primeiro cliente
        remaining_clients = set(range(1, self.dimension + 1))
        remaining_clients.remove(self.depot)  # Remove o depósito
        solution = []

        while remaining_clients:
            # Escolhe aleatoriamente um cliente para iniciar a rota
            current_node = random.choice(list(remaining_clients))
            route = [current_node]
            current_capacity = self.capacity - self.demands[current_node]
            remaining_clients.remove(current_node)

            # Adiciona mais clientes pela lógica de vizinho mais próximo
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
                    break

                route.append(closest_client)
                current_capacity -= self.demands[closest_client]
                remaining_clients.remove(closest_client)
                current_node = closest_client

            # Finaliza a rota retornando ao depósito
            solution.append([self.depot] + route + [self.depot])

        return solution

    def calculate_route_cost(self, route):
        """
        Calcula o custo (distância total) de uma rota específica,
        somando as distâncias entre nós consecutivos.
        """
        cost = 0.0
        for i in range(len(route) - 1):
            cost += self.distances[route[i] - 1][route[i + 1] - 1]
        return cost

    def calculate_solution_cost(self, solution):
        """
        Calcula o custo total de uma solução, que é a soma
        dos custos de cada rota na lista 'solution'.
        """
        total_cost = 0.0
        for route in solution:
            total_cost += self.calculate_route_cost(route)
        return total_cost


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


def check_route_capacity(route, demands, capacity):
    """
    Verifica se a soma das demandas dos clientes na rota
    não excede a capacidade. (Ignora depósitos, assumindo rota[0] e rota[-1] são depósitos)
    """
    total_demand = sum(
        demands[c] for c in route[1:-1]
    )  # exclui depósito inicial e final
    return total_demand <= capacity


def two_opt_move(instance, solution):
    """
    Aplica um movimento 2-opt em uma única rota escolhida aleatoriamente.
    - Não altera a distribuição de clientes entre as rotas (não afeta capacidade).
    - Apenas reverte um subtrecho da rota para tentar melhorar (ou modificar) o caminho.
    """

    # Copia a solução para não alterar o original
    new_solution = copy.deepcopy(solution)

    # Escolhe aleatoriamente uma rota que tenha pelo menos 4 nós
    # (2 nós de depósito + pelo menos 2 clientes)
    candidate_routes = [r for r in new_solution if len(r) > 3]
    if not candidate_routes:
        # Não há rota elegível (todas têm 3 ou menos nós?)
        return new_solution  # Retorna a cópia sem modificações

    route = random.choice(candidate_routes)
    # route é algo como [1, clienteA, clienteB, ..., 1]

    # Tenta fazer 2-opt no trecho entre (1..len(route)-2),
    # pois não mexemos no depósito inicial e final
    n = len(route)
    if n < 4:
        return new_solution  # Por precaução

    # Escolhe aleatoriamente duas posições i, j, com i < j
    # para reverter a subrota route[i:j+1]
    i = random.randint(1, n - 4)
    j = random.randint(i + 1, n - 3)
    i = 2
    j = 5

    # Reverte o subtrecho [i, j]
    route[i + 1 : j + 1] = reversed(route[i + 1 : j + 1])

    return new_solution


# Exemplo de uso
if __name__ == "__main__":
    # Carrega a instância
    instance = load_instance("./Vrp-Set-A/A/A-n32-k5.vrp")

    # Gera a solução inicial
    initial_solution = instance.generate_initial_solution()

    # Calcula e exibe o custo total da solução
    total_cost = instance.calculate_solution_cost(initial_solution)

    print("Solução Inicial (Cliente Aleatório + Vizinho Mais Próximo):")
    for i, route in enumerate(initial_solution, start=1):
        route_cost = instance.calculate_route_cost(route)
        print(f"Veículo {i}: {route} | Custo da Rota: {route_cost:.2f}")

    print(f"Custo Total da Solução: {total_cost:.2f}")
    print(f"Número de veículos (lido do nome): {instance.num_vehicles}")
