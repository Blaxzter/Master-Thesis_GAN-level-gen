import dash
import numpy as np
import plotly.graph_objects as go
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

from converter.to_img_converter.LevelImgEncoder import LevelImgEncoder
from data_scripts.CreateEncodingData import create_element_for_each_block
from level.Level import Level
from test.TestEnvironment import TestEnvironment
from test.visualization.LevelVisualisation import create_plotly_data

current_figure = None

if __name__ == '__main__':
    test_environment = TestEnvironment('generated/single_structure_small')

    level_img_encoder = LevelImgEncoder()

    app = dash.Dash(__name__)

    app.layout = html.Div([
        dcc.Markdown("# Level Visualisation"),
        html.Div([
            html.Div([
                dcc.Markdown("## Encoding"),
                dcc.Checklist(
                    id = "encoding",
                    options = [
                        {"label": 'Multilayer', "value": 'multi_layer'},
                        {"label": 'Only One', "value": 'only_one'},
                        {"label": 'Zero Included', "value": 'zero_included'},
                        {"label": 'One Hot', "value": 'one_hot'},
                    ],
                    value = ['multi_layer']
                )
            ], style = {'margin-right': '3em'}),
            html.Div([
                dcc.Markdown("## Level Selection"),
                dcc.Input(
                    id = "level_selection",
                    type = "number",
                    value = 0,
                    placeholder = "input type {}".format("number"),
                )],
            ),
            html.Div([
                dcc.Markdown("## Control"),
                dcc.Checklist(
                    id = "test_level",
                    options = [
                        {"label": 'Test Encoding', "value": 'test_encoding'}
                    ],
                    value = []
                )])
        ], style = {'display': 'flex'}),
        dcc.Graph(id = "voxel-chart", style = {'height': '90vh'}),
    ])

    @app.callback(
        Output("voxel-chart", "figure"),
        [
            Input("encoding", "value"),
            Input("level_selection", "value"),
            Input('test_level', 'value'),
        ]
    )
    def update_line_chart(encoding, level_selection, test_level):

        if 'test_encoding' not in test_level:
            level = test_environment.get_level(level_selection)
        else:
            elements = create_element_for_each_block()[0]
            level = Level.create_level_from_structure(elements)

        if 'only_one' in encoding:
            level_img = level_img_encoder.create_one_element_img(
                level.get_used_elements(),
                air_layer = 'zero_included' in encoding,
                multilayer = 'multi_layer' in encoding,
                true_one_hot = 'one_hot' in encoding
            )
        else:
            level_img = level_img_encoder.create_calculated_img(level.get_used_elements())

            if 'multi_layer' in encoding:
                level_img = level_img_encoder.create_multi_dim_img_from_picture(
                    level_img, with_air_layer = 'zero_included' in encoding)

        level_img = np.flip(level_img, axis = 0)

        plotly_data = create_plotly_data(level_img, true_one_hot = 'one_hot' in encoding)
        fig = go.Figure(data = plotly_data)
        fig.update_layout(scene = dict(
            aspectmode = 'data',
            camera = dict(
                up = dict(x = 0, y = 0, z = 1),
                eye = dict(x = 0., y = 0., z = 2.5),
                center = dict(x = 0, y = 0, z = 0),
            )
        ))

        fig.layout.uirevision = True
        global current_figure

        current_figure = fig
        return fig


    app.run_server(debug = True, port = 5052)
