import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from pypfopt import risk_models, expected_returns
import pandas as pd
import streamlit as st
import extra_streamlit_components as stx
from pypfopt.base_optimizer import BaseOptimizer
from pypfopt.discrete_allocation import DiscreteAllocation
from pypfopt.plotting import *
from sqlalchemy import Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    login = Column(String(100), primary_key=True)
    password = Column(String(100))

    def __repr__(self):
        return f'{self.login}:{self.password}'


cookie_manager = stx.CookieManager()


@st.cache_resource
def db_engine():
    engine = create_engine("postgresql://postgres:infin@postgres/postgres")
    Base.metadata.create_all(engine)
    return engine


@st.cache_data
def stocks():
    return pd.read_sql_table("quotes", db_engine()).set_index("index")


@st.cache_data
def tickers():
    return stocks().columns


@st.cache_data
def yearly_return():
    return expected_returns.mean_historical_return(stocks(), frequency=365)


def optimizer():
    df = stocks()
    S = risk_models.sample_cov(df)
    mu = yearly_return()
    return EfficientFrontier(mu, S)


@st.cache_data
def efficient_risk(risk):
    return optimizer().efficient_risk(risk)


@st.cache_data
def efficient_return(return_):
    return optimizer().efficient_return(return_)


@st.cache_data
def clean_ws(ws):
    cleaner = BaseOptimizer(len(tickers()), tickers())
    cleaner.set_weights(ws)
    ws = cleaner.clean_weights()
    return {k: v for k, v in ws.items() if v != 0}


def pct(value):
    return "{:1.1f}%".format(value)


# st.set_page_config(
#     page_title="InФин",
#     page_icon="💸",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )
st.header('💸InФин💸')
st.markdown("### Советы для Вашего *эффективного* портфеля")


def cabinet():
    try:
        st.write("Выберите показатель для оптимизации")
        mode = stx.tab_bar(data=[
            stx.TabBarItemData(id=1, title="Риск", description=""),
            stx.TabBarItemData(id=2, title="Доходность", description=""),
        ], default=1)
        if mode == '1':
            risk = st.slider("Выберите % риска", 10.0, 50.0)
            ws = efficient_risk(risk / 100)
        else:
            return_ = st.slider("Выберите % доходности", 0.0, 50.0)
            ws = efficient_return(return_ / 100)
    except (Exception, ValueError) as e:
        st.error("Невозможно построить портфель")
        return

    ws = clean_ws(ws)

    st.header("Портфель")
    left_column, right_column = st.columns(2)

    fig, ax = plt.subplots()
    ax.pie(
        ws.values(),
        labels=ws.keys(),
        autopct=pct,
    )
    left_column.pyplot(fig)

    summary = pd.DataFrame.from_dict(ws, orient="index", columns=["Доля"])
    summary["Доля"] = summary["Доля"].map(lambda it: pct(it * 100))
    returns = yearly_return().map(lambda it: pct(it * 100))
    returns.drop(
        labels=returns.index.difference(ws.keys()),
        inplace=True,
    )
    returns = returns.to_frame("Доходность")
    summary = summary.join(returns)
    right_column.write(summary)

    worst = min(ws.keys(), key=lambda k: ws[k])
    best = max(ws.keys(), key=lambda k: ws[k])

    if worst != best:
        if mode == 1:
            st.write(
                f"При заданном риске наиболее высокий доход приносит актив **{best}**, а наименьший доход приносит актив **{worst}**."
            )
        else:
            st.write(
                f"При заданном доходе наименее подверженный риску актив **{best}**, а наиболее подверженный актив **{worst}**."
            )

    st.header("Расчёт портфеля")
    cash = st.number_input("Начальные вложения (руб.)", min_value=1)
    latest_prices = stocks().tail(1).squeeze()
    allocator = DiscreteAllocation(ws, latest_prices=latest_prices, total_portfolio_value=cash)
    amounts, leftover = allocator.greedy_portfolio()
    amounts = pd.DataFrame.from_dict(amounts, orient="index", columns=["Количество акций"])
    st.write(amounts)
    st.write(f"Остаток средств: {round(leftover, 2)} руб.")

    st.header("Рыночные данные")
    st.write(stocks())


def login_menu():
    login = st.text_input("Логин")
    password = st.text_input("Пароль", type="password")

    login_button = st.button("Войти")
    sign_up_button = st.button("Зарегистрироваться")
    if sign_up_button:
        with Session(db_engine()) as session:
            with session.begin():
                session.add(User(login=login, password=password))
    if login_button or sign_up_button:
        cookie_manager.set("login", login)
        cookie_manager.set("password", password)


def logout_menu():
    st.sidebar.subheader(f"Приветствуем, {cookie_manager.get('login')}!")
    if st.sidebar.button("Выйти"):
        cookie_manager.delete("login")
        cookie_manager.delete("password")


login = cookie_manager.get("login")
password = cookie_manager.get("password")
with Session(db_engine()) as session:
    user = session.query(User).filter_by(login=login).first()
if user is None or user.password == password:
    login_menu()
else:
    cabinet()
    logout_menu()
