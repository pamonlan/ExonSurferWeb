import pandas as pd
import plotly.graph_objects as go
import plotly.offline as opy
import plotly.io as pio

from ExonSurfer.visualization import plot_rawseq

config = {"modeBarButtonsToRemove":[ "autoScale2d", "editInChartStudio", "editinchartstudio", \
                                    "hoverCompareCartesian", "hovercompare", "lasso", "lasso2d", "orbitRotation", \
                                    "orbitrotation", "pan", "pan2d", "pan3d", "reset", "resetCameraDefault3d", \
                                    "resetCameraLastSave3d", "resetGeo", "resetSankeyGroup",  \
                                    "resetViewMapbox", "resetViews", "resetcameralastsave", \
                                    "resetsankeygroup",  "resetview", "resetviews", "select", "select2d", \
                                    "sendDataToCloud", "senddatatocloud", "tableRotation", "tablerotation",  "toggleHover",\
                                    "toggleSpikelines", "togglehover", "togglespikelines"  "zoom2d", "zoom3d", \
                                    "zoomIn2d", "zoomInGeo", "zoomInMapbox", "zoomOut2d", "zoomOutGeo", "zoomOutMapbox", "zoomin", "zoomout"],
    'displaylogo': False,
    'toImageButtonOptions': {
        'format': 'svg', # one of png, svg, jpeg, webp
    }}

def plot_cdna(pair_id, final_df, species, release=108, file=False):
    """
    Function that highlights the OFF target alignment of the primers. 
    Used the primer_pair_id to get the alignment from the database
    Args:
        pair_id (int): Primer pair id
        final_df (dataframe): Dataframe returned by exon surfer
        species (str): Species name
        release (str): Release name
    Returns:
        html (str): cDNA in html format
    """
    try:
        html = plot_rawseq.highlight_ontarget(pair_id, final_df, species, release,file=file)
    except Exception as e:
        print("Error in plot_cdna", flush=True)
        print(e, flush=True)
    return html


def plot_off_target(pair_id, final_df, species,transcripts, release=108):
    """
    MAIN FUNCTION: highlights the OFF target alignment of the primers. 
    Args: 
        pair_id [in] (str)  Primer pair identifier (ex "Pair1")
        final_df [in] (str) Final design DF returned by exon surfer
        species [in] (str)  Organism
        strings [out] (l)   List of strings to write to the html file
    """
    try:
        lHtml = plot_rawseq.highlight_offtarget(pair_id, final_df, species, transcripts)
    except Exception as e:
        print("Error in plot_off_target", flush=True)
        print(e, flush=True)
        lHtml = []

    return lHtml

def plot_primerpair_aligment(transcripts, exons, primers, contig):
    """
    Function that take the transcripts, exons and primers and return a plotly figure
    Args:
        transcripts (dictionary): Dictionary with the exons of each transcript
        exons (dictionary): Dictionary with exons positions
        primers (dictionary): Dictionary with primers positions
    """

    # define colors for transcripts
    lCol =  ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', \
     '#999999', '#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02', '#a6761d', '#666666', \
     '#b3e2cd', '#fdb462', '#fb8072', '#80b1d3', '#fdb462', '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd', '#ccebc5', \
     '#ffed6f', '#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3', '#fdb462', '#b3de69', '#fccde5', '#d9d9d9', \
     '#bc80bd', '#ccebc5', '#ffed6f', '#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3', '#fdb462', '#b3de69', \
     '#fccde5', '#d9d9d9', '#bc80bd', '#ccebc5', '#ffed6f', '#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3']


    colors = dict(zip(transcripts.keys(),lCol))

    # define spacing between exon boxes
    box_spacing = 0.5

    # create the figure
    fig = go.Figure()

    # loop over transcripts
    for i, transcript in enumerate(transcripts):
        # create the transcript line
        fig.add_shape(type='line',
                    x0=min(exons[e][0] for e in transcripts[transcript]),
                    y0=i + 0.25,
                    x1=max(exons[e][1] for e in transcripts[transcript]),
                    y1=i + 0.25,
                    line=dict(color='black', width=2))

        # loop over exons in transcript
        for j, exon in enumerate(transcripts[transcript]):
            # determine x-coordinates of exon box
            x0 = exons[exon][0]
            x1 = exons[exon][1]
            width = x1 - x0

            # add exon box to figure
            fig.add_shape(type='rect',
                        x0=x0,
                        y0=i,
                        x1=x1,
                        y1=i + 0.5,
                        fillcolor=colors[transcript],
                        #line=dict(color='black'),
                        opacity=1
                        )
            # add hover with exon_id
            # Adding a trace with a fill, setting opacity to 0
            fig.add_trace(
                go.Scatter(
                    x=[x0 + width/2],
                    y=[i + 0.25],
                    mode='markers',
                    marker=dict(
                        size=0.1,
                        color=colors[transcript],
                        opacity=0
                    ),
                    hovertext=exon,
                    hoverinfo='text'
                )
            )

    # set x-axis range
    x_range = [min(exons[e][0] for t in transcripts.values() for e in t) - 1,
               max(exons[e][1] for t in transcripts.values() for e in t) + len(transcripts) * (box_spacing + 1)]
    fig.update_xaxes(range=x_range)

    # Add primers
    for primer in primers:
        fig.add_shape(type='line',
                    x0=primers[primer][0],
                    y0=0.2,
                    x1=primers[primer][1],
                    y1=0.2,
                    line=dict(color='black', width=3),
                    yref='paper')
        fig.add_annotation(text=primer,
                        x=(primers[primer][0]+primers[primer][1])/2,
                        y=0.1,
                        showarrow=False,
                        yref='paper')

    # set layout properties
    fig.update_layout(
        #title='Exon Plot',
        xaxis_title=f"Chr{contig}",
        #yaxis_title='Transcript',
        showlegend=False,
        #height=500,
        #width=800,
    )

    fig.update_layout(template="plotly_white")
    fig.update_layout(yaxis=dict(tickmode='array',
                                tickvals=[x + 0.25 for x in list(range(len(transcripts))) ],
                                ticktext=["<b> %s </b>"%x for x in list(transcripts.keys())],
                                range=[-0.6, len(transcripts)-0.4]))


    html = pio.to_html(fig, full_html=False, config=config)
    return html

def create_ex_css():
# Define list of colors
    lColors = ['#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#e6ab02', '#a6761d', '#666666']

    # Generate CSS code for classes .ex1 to .exN
    css_code = ''
    for i, color in enumerate(lColors):
        # Define class name and lighter color
        class_name = f'.ex{i+1}'
        lighter_color = '#%02x%02x%02x' % tuple(int(c, 16) + 30 for c in color[1:])
        
        # Generate CSS for normal and highlighted versions of class
        css_code += f"{class_name} {{color: {color}; display: inline;}}\n"
        css_code += f"{class_name}H {{color: {color}; background-color: {lighter_color}; display: inline;}}\n\n"

    # Print CSS code
    print(css_code)