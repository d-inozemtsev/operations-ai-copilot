import os

from langchain.agents import create_agent
from langchain.tools import tool

from app.scenario import calculate_scenario
from app.sources import get_inventory, get_sales, get_shipments

from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv

from langfuse import get_client
from langfuse.langchain import CallbackHandler

load_dotenv()

model = ChatOpenRouter(
    model=os.getenv("OPENROUTER_MODEL", "openrouter/free")
)

@tool
def current_inventory(product: str, city: str) -> int:
    """Узнать текущий остаток товара на складе указанного города."""
    return get_inventory(product, city)


@tool
def sales_history(product: str, city: str, days: int = 14) -> list[dict]:
    """Получить ежедневные продажи товара в городе за последние дни."""
    return get_sales(product, city, days)


@tool
def planned_shipments(product: str, city: str) -> list[dict]:
    """Узнать количество и сроки запланированных поставок товара в город."""
    return get_shipments(product, city)


@tool
def simulate_inventory(
    product: str,
    city: str,
    horizon_days: int = 14,
    demand_growth_pct: float = 0,
    shipment_delay_days: int = 0,
) -> dict:
    """Рассчитать запасы по дням при изменении спроса и задержке поставок."""
    return calculate_scenario(
        product=product,
        city=city,
        horizon_days=horizon_days,
        demand_growth_pct=demand_growth_pct,
        shipment_delay_days=shipment_delay_days,
    )

SYSTEM_PROMPT = """
Ты помощник по планированию запасов в демонстрационной системе.
Отвечай пользователю по-русски.

Доступные данные находятся только в предоставленных инструментах.
Не придумывай остатки, продажи, сроки поставок или результаты расчёта.

Если вопрос о текущем остатке, используй current_inventory.
Если вопрос об истории продаж, используй sales_history.
Если вопрос о запланированных поставках, используй planned_shipments.
Если вопрос о будущем запасе или сценарии «что если»,
обязательно используй simulate_inventory.
Самостоятельно прогноз по дням не вычисляй.

Передавай в инструменты названия городов так, как они записаны в данных:
Москва — Moscow, Казань — Kazan, Самара — Samara,
Новосибирск — Novosibirsk, Владивосток — Vladivostok.
Название PE-100 в вопросе соответствует коду PE100 в данных.

Если пользователь не указал период прогноза, возьми 14 дней.
Если он не указал изменение спроса или задержку поставок,
используй для них 0. Не добавляй изменения молча.

После расчёта назови исходный остаток, ожидаемый спрос в день,
день первой нехватки (если он есть) и остаток на конец периода.
Если данных для ответа нет, скажи об этом прямо.
"""

def ask_agent(question: str) -> str:

    agent = create_agent(
        model=model,
        tools=[
            current_inventory,
            sales_history,
            planned_shipments,
            simulate_inventory,
        ],
        system_prompt=SYSTEM_PROMPT,
    )

    langfuse = get_client()
    langfuse_handler = CallbackHandler()

    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"callbacks": [langfuse_handler]},
    )

    langfuse.flush()
    return result["messages"][-1].content