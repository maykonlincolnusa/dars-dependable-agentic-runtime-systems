import os
import json
import logging
from huggingface_hub import InferenceClient

logging.basicConfig(level=logging.INFO)

class BaseAgent:
    def __init__(self, environment, model="meta-llama/Meta-Llama-3-8B-Instruct"):
        self.env = environment
        self.model = model
        self.client = InferenceClient(model=self.model, token=os.getenv("HF_TOKEN"))
        
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "check_inventory",
                    "description": "Verifica o estoque atual de um item.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_id": {"type": "string", "description": "ID do produto (ex: 'X')"}
                        },
                        "required": ["item_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "order_item",
                    "description": "Solicita o pedido de um item para aumentar o estoque.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_id": {"type": "string", "description": "ID do produto"},
                            "quantity": {"type": "integer", "description": "Quantidade a pedir"}
                        },
                        "required": ["item_id", "quantity"]
                    }
                }
            }
        ]

    def execute_tool(self, tool_name, kwargs):
        if tool_name == "check_inventory":
            return self.env.check_inventory(**kwargs)
        elif tool_name == "order_item":
            return self.env.order_item(**kwargs)
        elif tool_name == "abort_task":
            return {"status": "aborted", "reason": kwargs.get("reason", "")}
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

class RetryAgent(BaseAgent):
    def run(self, task: str):
        messages = [{"role": "user", "content": task}]
        max_steps = 5
        
        for step in range(max_steps):
            try:
                response = self.client.chat_completion(
                    messages=messages,
                    tools=self.tools,
                    max_tokens=250
                )
                
                msg = response.choices[0].message
                # The chat_completion output might need adjustment to dict depending on the HF client version,
                # but we'll append it directly as it usually implements __dict__ or we can parse it.
                messages.append(msg)
                
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_name = tc.function.name
                        args = json.loads(tc.function.arguments)
                        logging.info(f"RetryAgent chamando {tool_name} com {args}")
                        
                        try:
                            result = self.execute_tool(tool_name, args)
                            messages.append({"role": "tool", "name": tool_name, "content": json.dumps(result)})
                        except Exception as e:
                            logging.warning(f"Erro na ferramenta {tool_name}: {e}")
                            # RETRY LOGIC: Apenas passa o erro para o modelo tentar de novo
                            messages.append({"role": "tool", "name": tool_name, "content": f"Erro: {str(e)}"})
                else:
                    return msg.content
                    
            except Exception as e:
                logging.error(f"Agent error: {e}")
                break
                
        return "Max steps reached or error."

class DependableAgent(BaseAgent):
    def __init__(self, environment, model="meta-llama/Meta-Llama-3-8B-Instruct"):
        super().__init__(environment, model)
        # Adiciona ferramenta de abstenção
        self.tools.append({
            "type": "function",
            "function": {
                "name": "abort_task",
                "description": "Aborta a tarefa de forma segura caso ocorra uma falha critica ou incerteza no estado.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {"type": "string"}
                    },
                    "required": ["reason"]
                }
            }
        })
        
    def run(self, task: str):
        system_prompt = (
            "Você é um agente dependável. Você DEVE verificar o estoque antes e DEPOIS de pedir um item. "
            "Se a ferramenta de pedido retornar um erro (como Timeout), NÃO tente pedir novamente imediatamente. "
            "Sempre verifique o estoque novamente para ver se o pedido passou. "
            "Se você não tiver certeza absoluta do estado, use a ferramenta abort_task."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task}
        ]
        
        max_steps = 7
        
        for step in range(max_steps):
            try:
                response = self.client.chat_completion(
                    messages=messages,
                    tools=self.tools,
                    max_tokens=250
                )
                
                msg = response.choices[0].message
                messages.append(msg)
                
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_name = tc.function.name
                        args = json.loads(tc.function.arguments)
                        logging.info(f"DependableAgent chamando {tool_name} com {args}")
                        
                        try:
                            result = self.execute_tool(tool_name, args)
                            messages.append({"role": "tool", "name": tool_name, "content": json.dumps(result)})
                            
                            if tool_name == "abort_task":
                                return f"Task aborted safely. Reason: {args.get('reason')}"
                                
                        except Exception as e:
                            logging.warning(f"Erro na ferramenta {tool_name}: {e}")
                            messages.append({"role": "tool", "name": tool_name, "content": f"Erro: {str(e)}. Verifique o estado atual com check_inventory antes de agir."})
                else:
                    return msg.content
                    
            except Exception as e:
                logging.error(f"Agent error: {e}")
                break
                
        return "Max steps reached or error."
