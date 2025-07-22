"""
一个简单的数据分析 Agent

INSTALLATION:
    %pip install -U langchain_experimental
    %pip install -U pandas numpy tabulate
"""
import os
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain.agents import AgentType
from langchain_openai import ChatOpenAI
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from dotenv import load_dotenv
import os

load_dotenv()
base_url = os.getenv("OPENAI_BASE_URL")
api_key = os.getenv("OPENAI_API_KEY")

# 随机种子（复现性）
np.random.seed(42)

# 生成样本数据
"""创建一个汽车销售的样本数据，包括生产日期、汽车品牌、型号、颜色和其他有关信息"""
# Generate sample data
n_rows = 1000

# Generate dates
start_date = datetime(2022, 1, 1)
dates = [start_date + timedelta(days=i) for i in range(n_rows)]

# 定义数据类别
makes = ['Toyota', 'Honda', 'Ford', 'Chevrolet', 'Nissan', 'BMW', 'Mercedes', 'Audi', 'Hyundai', 'Kia']
models = ['Sedan', 'SUV', 'Truck', 'Hatchback', 'Coupe', 'Van']
colors = ['Red', 'Blue', 'Black', 'White', 'Silver', 'Gray', 'Green']

# 创建数据集
data = {
    'Date': dates,
    'Make': np.random.choice(makes, n_rows),
    'Model': np.random.choice(models, n_rows),
    'Color': np.random.choice(colors, n_rows),
    'Year': np.random.randint(2015, 2023, n_rows),
    'Price': np.random.uniform(20000, 80000, n_rows).round(2),
    'Mileage': np.random.uniform(0, 100000, n_rows).round(0),
    'EngineSize': np.random.choice([1.6, 2.0, 2.5, 3.0, 3.5, 4.0], n_rows),
    'FuelEfficiency': np.random.uniform(20, 40, n_rows).round(1),
    'SalesPerson': np.random.choice(['Alice', 'Bob', 'Charlie', 'David', 'Eva'], n_rows)
}

# 创建 DataFrame 并按日期排序
df = pd.DataFrame(data).sort_values('Date')

# 显示生成数据的前几行和统计信息
print("\nFirst few rows of the generated data:")
print(df.head())

print("\nDataFrame info:")
df.info()

print("\nSummary statistics:")
print(df.describe())
"""
Example Output:
First few rows of the generated data:
        Date       Make      Model  Color  Year     Price  Mileage  EngineSize  FuelEfficiency SalesPerson
0 2022-01-01   Mercedes      Sedan  Green  2022  57952.65   5522.0         2.0            24.7       Alice
1 2022-01-02  Chevrolet  Hatchback    Red  2021  58668.22  94238.0         1.6            26.2         Bob
2 2022-01-03       Audi      Truck  White  2019  69187.87   7482.0         2.0            28.0       David
3 2022-01-04     Nissan  Hatchback  Black  2016  40004.44  43846.0         3.5            24.8       David
4 2022-01-05   Mercedes  Hatchback    Red  2016  63983.07  52988.0         2.5            24.1       Alice

DataFrame info:
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 1000 entries, 0 to 999
Data columns (total 10 columns):
 #   Column          Non-Null Count  Dtype
---  ------          --------------  -----
 0   Date            1000 non-null   datetime64[ns]
 1   Make            1000 non-null   object
 2   Model           1000 non-null   object
 3   Color           1000 non-null   object
 4   Year            1000 non-null   int32
 5   Price           1000 non-null   float64
 6   Mileage         1000 non-null   float64
 7   EngineSize      1000 non-null   float64
 8   FuelEfficiency  1000 non-null   float64
 9   SalesPerson     1000 non-null   object
dtypes: datetime64[ns](1), float64(4), int32(1), object(4)
memory usage: 74.3+ KB

Summary statistics:
                      Date         Year         Price       Mileage   EngineSize  FuelEfficiency
count                 1000  1000.000000   1000.000000   1000.000000  1000.000000     1000.000000
mean   2023-05-15 12:00:00  2018.445000  51145.360800  48484.643000     2.744500       29.688500
min    2022-01-01 00:00:00  2015.000000  20026.570000     19.000000     1.600000       20.000000
25%    2022-09-07 18:00:00  2017.000000  36859.940000  23191.500000     2.000000       24.500000
50%    2023-05-15 12:00:00  2018.000000  52215.155000  47506.000000     2.500000       29.700000
75%    2024-01-20 06:00:00  2020.000000  65741.147500  73880.250000     3.500000       34.700000
max    2024-09-26 00:00:00  2022.000000  79972.640000  99762.000000     4.000000       40.000000
std                    NaN     2.256117  17041.610861  29103.404593     0.839389        5.896316
"""



# 创建 Pandas DataFrame Agent，其能够分析数据集并回答相关问题
agent = create_pandas_dataframe_agent(
    ChatOpenAI(model="gpt-4.1-nano-2025-04-14", temperature=0, base_url=base_url, api_key=api_key),
    df,
    verbose=True,
    allow_dangerous_code=True,
    agent_type=AgentType.OPENAI_FUNCTIONS,
)
print("Data Analysis Agent is ready. You can now ask questions about the data.")

# 定义提问函数
def ask_agent(question):
    """Function to ask questions to the agent and display the response"""
    response = agent.invoke({
        "input": question,
        "agent_scratchpad": f"Human: {question}\nAI: To answer this question, I need to use Python to analyze the dataframe. I'll use the python_repl_ast tool.\n\nAction: python_repl_ast\nAction Input: ",
    })
    print(f"Question: {question}")
    print(f"Answer: {response}")
    print("---")


# 提问示例
ask_agent("What are the column names in this dataset?")
ask_agent("How many rows are in this dataset?")
ask_agent("What is the average price of cars sold?")
ask_agent("这里有什么数据？")
"""
Example Output:
> Entering new AgentExecutor chain...

Invoking: `python_repl_ast` with `{'query': 'list(df.columns)'}`


['Date', 'Make', 'Model', 'Color', 'Year', 'Price', 'Mileage', 'EngineSize', 'FuelEfficiency', 'SalesPerson']The column names in this dataset are:
- Date
- Make
- Model
- Color
- Year
- Price
- Mileage
- EngineSize
- FuelEfficiency
- SalesPerson

> Finished chain.
Question: What are the column names in this dataset?
Answer: {'input': 'What are the column names in this dataset?', 'agent_scratchpad': "Human: What are the column names in this dataset?\nAI: To answer this question, I need to use Python to analyze the dataframe. I'll use the python_repl_ast tool.\n\nAction: python_repl_ast\nAction Input: ", 'output': 'The column names in this dataset are:\n- Date\n- Make\n- Model\n- Color\n- Year\n- Price\n- Mileage\n- EngineSize\n- FuelEfficiency\n- SalesPerson'}
---


> Entering new AgentExecutor chain...

Invoking: `python_repl_ast` with `{'query': 'len(df)'}`


1000The dataset contains 1000 rows.

> Finished chain.
Question: How many rows are in this dataset?
Answer: {'input': 'How many rows are in this dataset?', 'agent_scratchpad': "Human: How many rows are in this dataset?\nAI: To answer this question, I need to use Python to analyze the dataframe. I'll use the python_repl_ast tool.\n\nAction: python_repl_ast\nAction Input: ", 'output': 'The dataset contains 1000 rows.'}
---


> Entering new AgentExecutor chain...

Invoking: `python_repl_ast` with `{'query': "average_price = df['Price'].mean()\naverage_price"}`


51145.360799999995The average price of the cars sold is approximately $51,145.36.

> Finished chain.
Question: What is the average price of cars sold?
Answer: {'input': 'What is the average price of cars sold?', 'agent_scratchpad': "Human: What is the average price of cars sold?\nAI: To answer this question, I need to use Python to analyze the dataframe. I'll use the python_repl_ast tool.\n\nAction: python_repl_ast\nAction Input: ", 'output': 'The average price of the cars sold is approximately $51,145.36.'}
---


> Entering new AgentExecutor chain...

Invoking: `python_repl_ast` with `{'query': 'df.head()'}`


        Date       Make      Model  Color  Year     Price  Mileage  EngineSize  FuelEfficiency SalesPerson
0 2022-01-01   Mercedes      Sedan  Green  2022  57952.65   5522.0         2.0            24.7       Alice
1 2022-01-02  Chevrolet  Hatchback    Red  2021  58668.22  94238.0         1.6            26.2         Bob
2 2022-01-03       Audi      Truck  White  2019  69187.87   7482.0         2.0            28.0       David
3 2022-01-04     Nissan  Hatchback  Black  2016  40004.44  43846.0         3.5            24.8       David
4 2022-01-05   Mercedes  Hatchback    Red  2016  63983.07  52988.0         2.5            24.1       Alice这份数据包含关于汽车销售的相关信息。具体包括以下字段：

- **Date（日期）**：销售的日期
- **Make（品牌）**：汽车品牌，例如奔驰、雪弗兰等
- **Model（车型）**：具体车型，如轿车、皮卡等
- **Color（颜色）**：汽车颜色
- **Year（年份）**：汽车制造年份
- **Price（价格）**：销售价格
- **Mileage（里程）**：汽车行驶的里程数
- **EngineSize（发动机排量）**：发动机的排量
- **FuelEfficiency（油耗）**：燃油效率（每加仑英里数或类似单位）
- **SalesPerson（销售员）**：负责销售的人员姓名

这些数据可以用来分析汽车销售情况、不同车型的表现、销售人员的业绩等。

> Finished chain.
Question: 这里有什么数据？
Answer: {'input': '这里有什么数据？', 'agent_scratchpad': "Human: 这里有什么数据？\nAI: To answer this question, I need to use Python to analyze the dataframe. I'll use the python_repl_ast tool.\n\nAction: python_repl_ast\nAction Input: ", 'output': '这份数据包含关于汽车销售的相关信息。具体包括以下字段：\n\n- **Date（日期）**：销售的日期\n- **Make（品牌）**：汽车品牌， 例如奔驰、雪弗兰等\n- **Model（车型）**：具体车型，如轿车、皮卡等\n- **Color（颜色）**：汽车颜色\n- **Year（年份）**：汽车制造年份\n- **Price（价格）**：销售价格\n- **Mileage（里程）**：汽车行驶的里程数\n- **EngineSize（发动机排量）**：发动机的排量\n- **FuelEfficiency（油耗）**：燃油效率（每加仑英里数或类似单位）\n- **SalesPerson（销售员）**：负责销售的人员姓名\n\n这些 数据可以用来分析汽车销售情况、不同车型的表现、销售人员的业绩等。'}
"""