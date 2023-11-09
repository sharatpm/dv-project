import pandas as pd
import numpy as np

import dash
from dash import dcc
from dash import html

import plotly.express as px
import plotly.graph_objects as go

app = dash.Dash()

county_data = pd.read_csv('datasets/county_data.csv')
state_code = pd.read_csv('datasets/state_codes.csv')
df = pd.merge(county_data, state_code, right_on = 'State', left_on = 'State')

df['BlackPop'] = (df['TotalPop'] * df['Black'] / 100).round().astype(np.int64)
df['WhitePop'] = (df['TotalPop'] * df['White'] / 100).round().astype(np.int64)
df['HispanicPop'] = (df['TotalPop'] * df['Hispanic'] / 100).round().astype(np.int64)
df['AsianPop'] = (df['TotalPop'] * df['Asian'] / 100).round().astype(np.int64)

black_by_state = df.groupby('Abbreviation')['BlackPop'].sum().reset_index()
black_by_state.columns = ['StateCode', 'Population']

asian_by_state = df.groupby('Abbreviation')['AsianPop'].sum().reset_index()
asian_by_state.columns = ['StateCode', 'Population']

hispanic_by_state = df.groupby('Abbreviation')['HispanicPop'].sum().reset_index()
hispanic_by_state.columns = ['StateCode', 'Population']

white_by_state = df.groupby('Abbreviation')['WhitePop'].sum().reset_index()
white_by_state.columns = ['StateCode', 'Population']

__tmp1df = pd.merge(white_by_state, hispanic_by_state, right_on='StateCode', left_on='StateCode')
__tmp1df.columns = ['StateCode', 'WhitePopulation', 'HispanicPopulation']

__tmp2df = pd.merge(black_by_state, asian_by_state, right_on='StateCode', left_on='StateCode')
__tmp2df.columns = ['StateCode', 'BlackPopulation', 'AsianPopulation']

minority_df = pd.merge(__tmp1df, __tmp2df, right_on='StateCode', left_on='StateCode')
total_pop_df = df.groupby('Abbreviation')['TotalPop'].sum().reset_index()
total_pop_df.columns = ['StateCode', 'TotalPopulation']

df['ProfessionalPop'] = (df['Professional'] * df['TotalPop'] / 100).round().astype(np.int64)
df['ServicePop'] = (df['Service'] * df['TotalPop'] / 100).round().astype(np.int64)
df['OfficePop'] = (df['Office'] * df['TotalPop'] / 100).round().astype(np.int64)
df['ConstructionPop'] = (df['Construction'] * df['TotalPop'] / 100).round().astype(np.int64)
df['ProductionPop'] = (df['Production'] * df['TotalPop'] / 100).round().astype(np.int64)

professional_df = df[[
    'Abbreviation',
    'ProfessionalPop',
    'ServicePop',
    'OfficePop',
    'ConstructionPop',
    'ProductionPop']].groupby('Abbreviation').sum().reset_index()
professional_df.rename(columns={'Abbreviation': 'StateCode'}, inplace=True)
melted_df = pd.melt(professional_df, id_vars='StateCode', var_name='Jobs', value_name='TotalPeople')
professional_melted_df = melted_df.sort_values('StateCode').reset_index().drop('index', axis=1, inplace=False)
px.treemap(professional_melted_df, path=['StateCode', 'Jobs'], values="TotalPeople")
professional_melted_df.to_csv('datasets/profession_count_by_state.csv', index=False)

app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1('US State Population Dashboard',
            style={'background-color':'lightblue',
                   'padding':'5px',
                   'border-top':'solid black 1px',
                   'border-bottom':'solid black 1px',
                   'text-align':'center'}),
    dcc.Dropdown(
        id='state-dropdown',
        options=state_code.rename(columns={"State": "label", "Abbreviation": "value"}).to_dict('records'),
        multi=True,
        value=['OK', 'CO', 'NM', 'KS']
    ),
    html.Div([
        html.Div([
            dcc.Graph(id='bar-chart', style={'width':'50%', 'height':'80vh'}),
            dcc.Graph(id='hierarchical-plot-treemap', style={'width':'50%', 'height':'80vh'})
        ],style={
            'width':'100%',
            'display':'flex',
            'flex-direction':'row',
        }), 
        html.Div([
            dcc.Graph(id='choropleth-map', style={'width':'50%', 'height':'80vh'}),
            dcc.Graph(id='strip-dot-chart', style={'width':'50%', 'height':'80vh'})
        ],style={
            'width':'100%',
            'display':'flex',
            'flex-direction':'row',
        }), 

    ],style={
        'display':'flex',
        'flex-direction':'column',
    }),  
])

@app.callback(
    [dash.dependencies.Output('choropleth-map', 'figure'),
     dash.dependencies.Output('bar-chart', 'figure'),
     dash.dependencies.Output('hierarchical-plot-treemap', 'figure'),
     dash.dependencies.Output('strip-dot-chart', 'figure')],
    [dash.dependencies.Input('state-dropdown', 'value')]
)

def update_plots(selected_states):
    filtered_df = total_pop_df[total_pop_df['StateCode'].isin(selected_states)]
    filtered_minority_df = minority_df[minority_df['StateCode'].isin(selected_states)]
    filtered_professional_df = professional_melted_df[professional_melted_df['StateCode'].isin(selected_states)]
    bar_chart = go.Figure(data=[
    go.Bar(name='Black', x=filtered_minority_df['StateCode'].values.tolist(), y=minority_df['BlackPopulation'].values.tolist()),
    go.Bar(name='Hispanic', x=filtered_minority_df['StateCode'].values.tolist(), y=minority_df['HispanicPopulation'].values.tolist())
    ])
    choropleth_map = px.choropleth(
        filtered_df,
        locations='StateCode',
        locationmode='USA-states',
        color='TotalPopulation',
        title='Statewise Population',
        scope='usa',
    )
    treemap_chart = px.sunburst(filtered_professional_df, path=['StateCode', 'Jobs'], values="TotalPeople")
    strip_chart = px.strip(df, y='IncomePerCap', hover_data=['State', 'County', 'IncomePerCap'], width=200)

    return choropleth_map, bar_chart, treemap_chart, strip_chart

if __name__ == '__main__':
    app.run_server(port=8080, debug=True)