import os
from dotenv import load_dotenv
from datasets import Dataset
from environment import Environment, FaultInjector
from agents import RetryAgent, DependableAgent

load_dotenv()

def load_evaluation_dataset():
    """
    Simula o carregamento de um dataset usando a biblioteca Hugging Face 'datasets'.
    No futuro, você poderá trocar isso por: load_dataset('nome_do_dataset_no_hub')
    """
    data = {
        "task_id": ["T1", "T2", "T3"],
        "instruction": [
            "Verifique o estoque do item 'X'. Se for menor que 10, encomende o suficiente para atingir 50 unidades no total.",
            "Consulte quantos itens 'X' temos. Precisamos garantir que haja exatamente 100 no estoque. Peça o restante.",
            "Estou preocupado com a falta do produto 'X'. Verifique o inventário. Se estiver zerado, peça 20."
        ],
        "target_stock": [50, 100, 20] # Ground truth para avaliação automática
    }
    return Dataset.from_dict(data)

def run_experiment():
    print("--- DARS: Benchmark com Hugging Face Datasets ---\n")
    
    if not os.getenv("HF_TOKEN"):
        print("AVISO: HF_TOKEN não encontrado no .env")
        print("Crie um arquivo .env com seu HF_TOKEN para o código se comunicar com a Hugging Face.")
        return
        
    dataset = load_evaluation_dataset()
    print(f"Dataset carregado com {len(dataset)} tarefas de teste.\n")
    
    # Vamos avaliar a primeira tarefa como prova de conceito
    sample = dataset[0]
    task = sample["instruction"]
    print(f"Avaliando Tarefa [{sample['task_id']}]: {task}\n")
    
    print("[Cenário 1] RetryAgent com Injeção de Falha (Late Timeout)")
    fault_injector_1 = FaultInjector()
    fault_injector_1.set_fault("late_timeout")
    env_1 = Environment(fault_injector_1)
    agent_1 = RetryAgent(env_1)
    
    print(f"Estoque Inicial: {env_1.db.inventory['X']}")
    agent_1.run(task)
    print(f"Estoque Final (Mock DB): {env_1.db.inventory['X']} | Target Ground Truth: {sample['target_stock']}")
    print(f"Pedidos processados (Alerta para Duplicação): {env_1.db.orders}")
    
    print("\n------------------------------------------------------\n")
    
    print("[Cenário 2] DependableAgent com Injeção de Falha (Late Timeout)")
    fault_injector_2 = FaultInjector()
    fault_injector_2.set_fault("late_timeout")
    env_2 = Environment(fault_injector_2)
    agent_2 = DependableAgent(env_2)
    
    print(f"Estoque Inicial: {env_2.db.inventory['X']}")
    agent_2.run(task)
    print(f"Estoque Final (Mock DB): {env_2.db.inventory['X']} | Target Ground Truth: {sample['target_stock']}")
    print(f"Pedidos processados (Seguro): {env_2.db.orders}")

if __name__ == "__main__":
    run_experiment()
