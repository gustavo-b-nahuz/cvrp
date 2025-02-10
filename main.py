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


def swap_move(instance, solution, max_attempts=10):
    """
    Realiza um movimento de Swap:
    - Escolhe dois clientes distintos (podem estar na mesma rota ou em rotas diferentes)
    - Tenta trocar de posição, checando a capacidade se as rotas forem diferentes.
    - max_attempts define quantas tentativas fazemos antes de desistir.

    Retorna um novo vizinho se encontrar um swap viável,
    caso contrário pode retornar a solução original (cópia).
    """

    new_solution = copy.deepcopy(solution)
    demands = instance.demands
    capacity = instance.capacity

    # Obtem todas as posições (rota, índice_na_rota) possíveis, exceto depositos
    # route[i] do tipo [1, c1, c2, ..., 1]. Vértices de depósito são 0 e len(route)-1.
    valid_positions = []
    for r_idx, route in enumerate(new_solution):
        for pos in range(1, len(route) - 1):
            valid_positions.append((r_idx, pos))

    if len(valid_positions) < 2:
        return new_solution  # Não há como fazer swap

    attempts = 0
    while attempts < max_attempts:
        attempts += 1

        # Escolhe duas posições distintas aleatoriamente
        i1, i2 = random.sample(valid_positions, 2)

        r1, pos1 = i1
        r2, pos2 = i2

        route1 = new_solution[r1]
        route2 = new_solution[r2]

        client1 = route1[pos1]
        client2 = route2[pos2]

        # Se for o mesmo cliente (improvável, mas pode acontecer se tiver repetição?), ignore
        if client1 == client2:
            continue

        # Caso a troca envolva duas rotas diferentes, precisamos checar capacidade
        if r1 != r2:
            # Capacidade livre na rota 1 (antes do swap)
            # Calcula demanda total da rota 1
            demand_r1 = sum(demands[c] for c in route1[1:-1])
            # Se tirarmos client1 e colocarmos client2, a nova demanda será:
            demand_r1_new = demand_r1 - demands[client1] + demands[client2]

            # Mesmo raciocínio para rota 2
            demand_r2 = sum(demands[c] for c in route2[1:-1])
            demand_r2_new = demand_r2 - demands[client2] + demands[client1]

            if demand_r1_new > capacity or demand_r2_new > capacity:
                # Não cabe
                continue

        # Se chegou aqui, a troca é viável
        route1[pos1], route2[pos2] = route2[pos2], route1[pos1]
        return new_solution

    # Se não encontrou nada viável depois de N tentativas, retorna sem mudança
    return new_solution


def or_opt_move(instance, solution, max_attempts=10, max_block_size=3):
    """
    Movimento Or-Opt:
    - Remove um bloco (1..max_block_size) de clientes consecutivos de uma rota
      e insere em outra posição (pode ser na mesma rota ou em outra),
      desde que a capacidade seja respeitada.
    - Tenta max_attempts vezes encontrar um movimento viável.

    Retorna a nova solução se encontrar movimento, senão retorna a cópia original.
    """

    new_solution = copy.deepcopy(solution)
    demands = instance.demands
    capacity = instance.capacity

    # Filtra rotas que possuam pelo menos 3 nós (deposito + 1 cliente + deposito)
    candidate_routes = [idx for idx, r in enumerate(new_solution) if len(r) > 3]

    if not candidate_routes:
        # Nenhuma rota tem clientes suficientes
        return new_solution

    attempts = 0
    while attempts < max_attempts:
        attempts += 1

        # Escolhe aleatoriamente uma rota de origem e uma de destino
        r_orig_idx = random.choice(candidate_routes)
        r_dest_idx = random.choice(
            range(len(new_solution))
        )  # pode ser a mesma ou outra

        route_orig = new_solution[r_orig_idx]
        route_dest = new_solution[r_dest_idx]

        # Define um tamanho de bloco aleatório
        block_size = random.randint(1, max_block_size)

        # Posições possíveis de remoção (não remover depósitos!)
        # route_orig: [1, c1, c2, ..., cN, 1] => índices válidos: 1..len-2
        if len(route_orig) - 2 < 1:
            # rota com 0 clientes?
            continue

        start_pos = random.randint(1, len(route_orig) - 2)  # Índice do primeiro cliente
        end_pos = start_pos + block_size - 1  # Índice do último cliente no bloco
        if end_pos >= len(route_orig) - 1:
            continue  # bloco passa do final?

        # Extrai esse bloco de clientes
        block = route_orig[start_pos : end_pos + 1]

        # Remove do original
        del route_orig[start_pos : end_pos + 1]

        # Agora tentamos inserir esse bloco em route_dest
        # Posições válidas de inserção em route_dest: 1..len(route_dest)-1
        insert_positions = list(range(1, len(route_dest)))

        # Tenta inserir em alguma posição
        inserted = False
        random.shuffle(insert_positions)  # para não ficar determinístico
        for ins_pos in insert_positions:
            # Faz inserção temporária
            route_dest[ins_pos:ins_pos] = block

            # Verifica capacidade da rota de destino e da rota de origem
            if check_route_capacity(
                route_dest, demands, capacity
            ) and check_route_capacity(route_orig, demands, capacity):
                inserted = True
                break
            else:
                # Desfaz inserção
                del route_dest[ins_pos : ins_pos + len(block)]

        if inserted:
            return new_solution
        else:
            # Precisamos recolocar o bloco na rota origem se falhou inserir
            route_orig[start_pos:start_pos] = block

    # Não encontrou um movimento viável depois de max_attempts
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
