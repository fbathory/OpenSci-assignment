# Create figures for the paper 
# Global flows and rates of international migration of scholars
#%%
##############################################################################
# Install packages if needed
# install duckdb:
# %pip install duckdb --upgrade --user
#%%
# to export as pdf we need python-kaleido
# (according to https://plotly.com/python/static-image-export/ )
# %conda install -c conda-forge python-kaleido
#%%
##############################################################################

#%%
# change this to "scopus" or "openalex" to switch between the two data providers:
data_provider=["openalex", "scopus"][1]

path_input = "./data_input/"
path_processed = "./data_processed/"
path_plots = "./FIGURES/"

fn_country_enriched =  f"{path_processed}{data_provider}_2024_V1_scholarlymigration_country_enriched.parquet" 
fn_flows_enriched = f"{path_processed}{data_provider}_2024_V1_scholarlymigration_countryflows_enriched.parquet"


#%%
import pandas as pd
import duckdb

con = duckdb.connect(':memory:')
# show all columns and rows:
pd.set_option('display.max_columns', 80)
pd.set_option('display.max_rows', 70)
print("duckdb version:", duckdb.__version__)
#%%
##############################################################################
# load country data and flows data
q = f"""SELECT * FROM '{fn_country_enriched}'"""
dfcountry = con.execute(q).df()
print(dfcountry.columns)

q = f"""SELECT * FROM '{fn_flows_enriched}'"""
dfflow = con.execute(q).df()
print(dfflow.columns)
#%%
##############################################################################
#select 15 countries with the highest number of avg_paddedpop_min:
countrylist = dfflow[dfflow.year==2018].groupby(
    ["countrynamefrom"]).mean("paddedpopfrom").sort_values(
        by='paddedpopfrom', ascending=False).head(15)#.sort_values("paddedpopfrom")#.countrynamefrom.unique()
countrylist = list(countrylist.index)
print(countrylist)
# scopus:
# ['China', 'United States', 'India', 'Japan', 'Germany', 'United Kingdom', 'Brazil', 'Italy', 'France', 'Spain', 'Korea, Rep.', 'Russian Federation', 'Canada', 'Australia', 'Iran, Islamic Rep.']
# openalex:
# ['United States', 'China', 'Japan', 'India', 'Germany', 'Brazil', 'United Kingdom', 'France', 'Italy', 'Spain', 'Russian Federation', 'Canada', 'Indonesia', 'Iran, Islamic Rep.', 'Australia']
# hardcode the scopus list, so the figures are more comparable:
countrylist = ['China', 'United States', 'India', 'Japan', 'Germany', 'United Kingdom', 'Brazil', 'Italy', 'France', 'Spain', 'Korea, Rep.', 'Russian Federation', 'Canada', 'Australia', 'Iran, Islamic Rep.']
#%%
# create a subset of the flows data for the 15 selected countries:
df = dfflow[(dfflow.year==2018) & (dfflow.countrynamefrom.isin(countrylist)) & (dfflow.countrynameto.isin(countrylist))]
df = df[['countrynamefrom', 'countrynameto', 'n_migrations', 'normalized_migration1', 'normalized_migration2']]
df.columns = ['country_source', 'country_destination', 'number_migrations', 'normalized_migration1', 'normalized_migration2']
print(df.country_source.nunique(),df.country_source.unique())

# %%
###############################################################################
# plot flows as heatmap:

import seaborn as sns
import plotly.express as px

# rename the values "Russian Federation" to "Russia" and "United States" to "USA" and "United Kingdom" to "UK"
# (saves space in the plot)
df['country_source'] = df['country_source'].replace('Russian Federation', 'Russia')
df['country_source'] = df['country_source'].replace('United States', 'USA')
df['country_source'] = df['country_source'].replace('United Kingdom', 'UK')
df['country_source'] = df['country_source'].replace('Iran, Islamic Rep.', 'Iran')
df['country_destination'] = df['country_destination'].replace('Russian Federation', 'Russia')
df['country_destination'] = df['country_destination'].replace('United States', 'USA')
df['country_destination'] = df['country_destination'].replace('United Kingdom', 'UK')
df['country_destination'] = df['country_destination'].replace('Iran, Islamic Rep.', 'Iran')

pivot_df = df.pivot(index='country_source', columns='country_destination', values='number_migrations')
pivot_df_normalized = df.pivot(index='country_source', columns='country_destination', values='normalized_migration2')
# y-axis label: source country
# x-axis label: destination country
# font-size of the countries: 5

# adjust the colorscale so that it is meaningful for both data providers:
vmax = pivot_df.mean().mean() * 2.4
print("vmax:", vmax)

bb = sns.heatmap(pivot_df_normalized, cmap='Blues', linewidths=0.5, annot=pivot_df, fmt='g',
   annot_kws={"size": 5}, square=True, vmin=0, vmax=vmax, #cbar_kws={'label': 'Number of migrants'},
    cbar=False, 
)
bb.set_xticklabels(bb.get_xticklabels(), rotation=90, horizontalalignment='right')
bb.set_yticklabels(bb.get_yticklabels(), rotation=0, horizontalalignment='right')
bb.tick_params(labelsize=7)
# set font of title:
bb.title.set_fontsize(10)

bb.set_title('Flow of scholarly migrants in 2018')
bb.set_xlabel('Destination country')
bb.set_ylabel('Source country')

# plt.show()

fig = bb.get_figure()
fig.subplots_adjust(bottom=0.29,left=0.01)
fn =f'{path_plots}FIG_5_1_{data_provider}_flow_heatmap.pdf'
bla = fig.savefig(fn,dpi=300)

# %%
###############################################################################
# hover data is needed for some figures below
hover_data={
            'countryname':True,
            'outmigrationrate':True, 
            # 'padded_population_of_researchers':True,
            'padded_population_of_researchers':True,
            'year':True,
        }

# define colors for all relevant countries:
country_colors = {
    'China': '#DD7464',  
    'United States': '#0000FF', 
    'Japan': '#5DEADF', 
    'Germany': '#E59D45', 
    'United Kingdom': '#7C84F2', 
    'Korea, Rep.': '#003478', 
    'Canada': '#C3F57D', 
    'Australia': '#5DEADF', 
    'UK': '#7C84F2', 
    'USA': '#0000FF',
}

# plot flow from one country to some other countries as line plot:

for country_source in ["United States"]:# ["Germany", "United Kingdom", "United States", "Japan", "China", "Brazil"]:
    # select the 5 countries with the highest number of migrants from the source country:
    destinations = dfflow[(dfflow.countrynamefrom==country_source)&(dfflow.avg_paddedpop_min>1000)].groupby(
        'countrynameto').agg({'n_migrations':'sum'}).sort_values("n_migrations", ascending=False).head(5).index
    print(destinations)
    # select the data for the source country and the 5 countries with the highest number of migrants:
    df1tomany = dfflow[(dfflow.countrynamefrom==country_source)&(dfflow.countrynameto.isin(destinations))]

    # add values for "other countries" to the dataframe (sum of all other countries):
    df1tomany.sort_values(by=['year'], inplace=True)
    df1tomany.rename({'countrynamefrom':'country_source', 'countrynameto':'country_destination'}, axis=1, inplace=True)
    fig1 = px.line(df1tomany, x="year", y="n_migrations", color_discrete_map=country_colors,
                            color="country_destination",log_y=True,line_shape="linear", render_mode="svg",
                            hover_name="year", #text="iso3codeto",#range_y=[0.015,0.075],
                            hover_data=[f"n_migrations",f"normalized_migration1",f"normalized_migration2"],
)
    fig1.update_traces(textposition='top center')
    fig1.update_layout(title=f"Flow of scholarly migrants from the {country_source} to top destinations",
                        xaxis_title="Year",    
                        yaxis_title=f"Number of scholarly migrants", # from the {country_source} to ...",
                        font=dict(size=12, color="#7f7f7f"),
                        plot_bgcolor='rgba(0,0,0,0)',
                        # xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=False),
                        legend_title_text='Destination country'
                      )
    # change y-axis to show the number of migrants in millions:
    fig1.update_yaxes(tickformat=".0f")
    fig1.show()
    fig1.write_image(f"{path_plots}FIG_4_4_{data_provider}_flow_over_time_{country_source}_to_othercountries.pdf")


# %%
###############################################################################
# plot flow from some countries to a specific country as a line plot (over time):

for country_destination in  ["United States"]:#["Germany", "United Kingdom", "United States", "Japan", "China", "Brazil"]:

    origins = dfflow[(dfflow.countrynameto==country_destination)&(dfflow.avg_paddedpop_min>1000)].groupby(
        'countrynamefrom').agg({'n_migrations':'sum'}).sort_values("n_migrations", ascending=False).head(5).index
    print(origins)
    # select the data for the source country and the 5 countries with the highest number of migrants:
    df1tomany = dfflow[(dfflow.countrynameto==country_destination)&(dfflow.countrynamefrom.isin(origins))]
    df1tomany.sort_values(by=['year'], inplace=True)
    df1tomany.rename({'countrynamefrom':'country_source', 'countrynameto':'country_destination'}, axis=1, inplace=True)
    fig1 = px.line(df1tomany, x="year", y="n_migrations", color_discrete_map=country_colors,
                            color="country_source",log_y=True,line_shape="linear", render_mode="svg",
                            hover_name="year", # text="iso3codefrom",#range_y=[0.015,0.075],
                            hover_data=[f"n_migrations",f"normalized_migration1",f"normalized_migration2"])
    fig1.update_traces(textposition='top center')
    fig1.update_layout(title=f"Flow of scholarly migrants to the {country_destination}",
                        xaxis_title="Year",
                        yaxis_title=f"Number of scholarly migrants", # from ... to {country_destination}",
                        font=dict(size=12, color="#7f7f7f"),
                        plot_bgcolor='rgba(0,0,0,0)',
                        # xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=False),
                        legend_title_text='Source country'
                    )
    # change y-axis to show the number of migrants in millions:
    fig1.update_yaxes(tickformat=".0f")
    # change the legend title
    fig1.show()
    fig1.write_image(f"{path_plots}FIG_4_3_{data_provider}_flow_over_time_othercountries_to_{country_destination}.pdf")

# %%
###############################################################################
# plot single country numbers as world-maps:
###############################################################################

startyear = 2013
endyear = 2017

#%%
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

###############################################################################
# Aggregate single country rates over a perios of some years:

dfmigrouped = dfcountry[(dfcountry["year"] >= startyear ) & (dfcountry["year"] <= endyear )].groupby("countrycode").agg(
        {
            "number_of_inmigrations":"mean",
            "number_of_outmigrations":"mean",
            "netmigration":"mean",
            #"paddedpop":"mean",
            "padded_population_of_researchers":"mean",
            "year":"mean",
            "countryname":"first",
            "iso3code":"first"
        })
# calculate rates:
dfmigrouped["outmigrationrate"] = dfmigrouped["number_of_outmigrations"]/dfmigrouped["padded_population_of_researchers"]
dfmigrouped["inmigrationrate"] = dfmigrouped["number_of_inmigrations"]/dfmigrouped["padded_population_of_researchers"]
dfmigrouped["netmigrationrate"] = dfmigrouped["netmigration"]/dfmigrouped["padded_population_of_researchers"]
dfmigrouped["Net migration rate"] = dfmigrouped["netmigration"]/dfmigrouped["padded_population_of_researchers"]
worldwide_total_researchers_in_period = dfmigrouped["padded_population_of_researchers"].sum()
print(f"{worldwide_total_researchers_in_period=}")

#%%
###############################################################################
# Net migration rates as world-map:

fig = px.choropleth(dfmigrouped.reset_index(),
          locations='iso3code',
          locationmode='ISO-3',
          color="Net migration rate",
          range_color=[-0.015,0.015],
          color_continuous_scale = "Temps_R",#color_continuous_scale,
          projection="robinson",
          scope='world',
          hover_data =hover_data
          )

fig.update_layout(coloraxis_colorbar=dict(
        yanchor="top", 
        y=0.95, x=0,
        ticks="outside",
        ticksuffix="",
        title=""))
fig.update_layout(title={
        'text': f"<b>Net migration rate, {startyear} - {endyear}",
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
        font=dict(size=12),#, color="#7f7f7f")
        legend_title_text=""
    )
    
# choose angle and center so we see everything except antarctica:
fig.update_geos(
    visible=False,showcountries=True,
    center=dict(lon=4, lat=19),
    lataxis_range=[-74,76], lonaxis_range=[-142, 167]
)
# remove the border around the world:
fig.update_traces(marker_line_width=0)
# fig.show()

#save as pdf:

fig.update_layout(width =900, height=490, font_size=13,
              font_family="Helvetica",
              margin_l=0, margin_t=12, margin_b=1, margin_r=0)
fig.write_image(f"{path_plots}FIG_3_{data_provider}_worldmap_country_migration_rates_net3.pdf")

#%%
###############################################################################
# Plot Kendall's tau correlation between OpenAlex and Scopus population rates
# Author: Aliakbar Akbaritabar

import pandas as pd
import os
import plotnine as gg

# load merged data, this data is created in 02_merge_openalex_scopus.py :
oascp = pd.read_csv(os.path.join(path_processed, 'dfmerged_openalex_scopus_country.csv'), dtype='str')


# calculate a correlation between OpenAlex and Scopus yearly population rates
correlation_res_pop = (
    oascp
    .dropna(subset=['countrycode', 'year', 'paddedpop_openalex', 'paddedpop_scopus'])
    .astype({'paddedpop_openalex':float, 'paddedpop_scopus':float, 'year':float})
    # limit years to 1998 - 2018 (inclusive)
    .query('year > 1997 & year < 2019')
    .sort_values(by=['countrycode', 'year'])
    .groupby('countrycode')
    [['paddedpop_openalex', 'paddedpop_scopus']]
    # change correlation method here to kendall or spearman
    .corr(method='kendall')
    .reset_index()
    .drop_duplicates(subset='countrycode')
    .rename(columns={'paddedpop_scopus': 'pop_kendal_corr'})
    [['countrycode', 'pop_kendal_corr']]
    .sort_values(by=['pop_kendal_corr'])
)


# join correlation results back to table to plot
oascp = oascp.merge(correlation_res_pop, how='left', on='countrycode')

# plot it as boxplot with jitter

FIG_2_1_kendal_pop = (
    gg.ggplot((
        oascp
        .drop_duplicates(subset=['countrycode', 'pop_kendal_corr'])
        .dropna(subset=['region'])
    ), gg.aes(x='factor(region)', y='pop_kendal_corr'))
    + gg.geom_jitter(height = 0, color='#d7d7d2')
    + gg.geom_boxplot(color='blue', fill=None)
    + gg.scale_y_continuous(limits=(-1, 1), breaks=[-1, -0.75, -0.50, -0.25, 0, 0.25, 0.50, 0.75, 1])
    + gg.labs(x="Countries based on region", y="Kendal Tau Correlation", title = 'Kendal tau correlation between \n\n Scopus and OpenAlex populations')
    + gg.theme_bw()
    + gg.theme(axis_text_x=gg.element_text(hjust=1, size=10, angle=45),
               figure_size=(5, 5))
)

gg.ggplot.save(FIG_2_1_kendal_pop, os.path.join(
    path_plots, 'FIG_2_1_kendal_pop.pdf'), limitsize=False)


# calculate a correlation between OpenAlex and Scopus yearly netmigration rates
correlation_res_netmig = (
    oascp
    .dropna(subset=['countrycode', 'year', 'netmigrate_openalex', 'netmigrate_scopus'])
    .astype({'netmigrate_openalex':float, 'netmigrate_scopus':float, 'year':float})
    # limit years to 1998 - 2018 (inclusive)
    .query('year > 1997 & year < 2019')
    .sort_values(by=['countrycode', 'year'])
    .groupby('countrycode')
    [['netmigrate_openalex', 'netmigrate_scopus']]
    # change correlation method here to kendall or spearman
    .corr(method='kendall')
    .reset_index()
    .drop_duplicates(subset='countrycode')
    .rename(columns={'netmigrate_scopus': 'nmr_kendal_corr'})
    [['countrycode', 'nmr_kendal_corr']]
    .sort_values(by=['nmr_kendal_corr'])
)

# join correlation results back to table to plot
oascp = oascp.merge(correlation_res_netmig, how='left', on='countrycode')


# plot it as boxplot with jitter

FIG_2_2_kendal_netmig = (
    gg.ggplot((
        oascp
        .drop_duplicates(subset=['countrycode', 'nmr_kendal_corr'])
        .dropna(subset=['region'])
    ), gg.aes(x='factor(region)', y='nmr_kendal_corr'))
    + gg.geom_jitter(height = 0, color='#d7d7d2')
    + gg.geom_boxplot(color='blue', fill=None)
    + gg.scale_y_continuous(limits=(-1, 1), breaks=[-1, -0.75, -0.50, -0.25, 0, 0.25, 0.50, 0.75, 1])
    + gg.labs(x="Countries based on region", y="Kendal Tau Correlation", title = 'Kendal tau correlation between \n\n Scopus and OpenAlex net migration rates')
    + gg.theme_bw()
    + gg.theme(axis_text_x=gg.element_text(hjust=1, size=10, angle=45),
               figure_size=(5, 5))
)

gg.ggplot.save(FIG_2_2_kendal_netmig, os.path.join(
    path_plots, 'FIG_2_2_kendal_netmig.pdf'), limitsize=False)


# %%
