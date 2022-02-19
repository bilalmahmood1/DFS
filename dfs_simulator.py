
## Set of libraries used
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from numpy.random import normal
import base64
from fuzzywuzzy import fuzz

## Set up seed for testing
np.random.seed(1)


## Helper functions
@st.cache
def convert_df(df):
    """Encode the df into csv file for downloading purpose"""
    return df.to_csv(index = False).encode('utf-8')

## Page layput
st.set_page_config(
    page_title="SIM",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# This is an implementation of Monte carlo simulation in order to rank lineups"
    }
)


def find_potential_matches(player_info_database, name, n = 5):
    candidates = sorted([(fuzz.token_sort_ratio(key, name), key) for key in player_info_database], reverse = True)[:n]
    return [n[1] for n in candidates]

def find_players_lineups(lineups_database):
    """Find all the names of the players in the lineups"""
    lineup_players = set()
    for i in lineups_database:
        lineup_players = lineup_players.union(set(i["player_names"]))
    return list(lineup_players)


def find_player_in_the_mapping_table(df_names, name):
    """Find all the player names in the names mapping table"""
    return list(df_names[df_names["lineup name"] == name]["statistics name"].values)


## Title and logo Image
st.title('DFS Simulator')
image = Image.open('images/logo.png')
st.image(image, use_column_width = False, caption='Monte Carlo Simulation')


## Total lineups
total_entries = st.sidebar.number_input('Contest Size', min_value = 1, step = 1, value =  2000)
st.write('Total Entries: ', total_entries)


## Number of simulations
number_sims = st.sidebar.number_input('Number of simulations', min_value = 1, max_value = 50000, step = 1, value =  2000)
st.write('Total Simulations: ', number_sims)


## Number of simulations
number_sims = st.sidebar.number_input('Number of simulations', min_value = 1, max_value = 50000, step = 1, value =  2000)
st.write('Total Simulations: ', number_sims)

## Display intermediate results
display = st.sidebar.radio("Show intermediate results?",('No', 'Yes'))


## Upload files
st.sidebar.header("Simulation Inputs")
# Statistics
uploaded_file_statistics = st.sidebar.file_uploader("Upload Player Statistics", type=["csv"])
if uploaded_file_statistics is not None:
    df_fd = pd.read_csv(uploaded_file_statistics)
    st.subheader("Player Statistics")
    st.write("There are %d rows and %d columns in Player statistics file" %(df_fd.shape[0],df_fd.shape[1]))
    st.write(df_fd)

# Lineups 
uploaded_file_lineups = st.sidebar.file_uploader("Upload Lineups", type=["csv"])
if uploaded_file_lineups is not None:
    df_crunch = pd.read_csv(uploaded_file_lineups)
    
    st.subheader("Lineups")
    st.write("There are %d rows and %d columns in Lineups file" %(df_crunch.shape[0],df_crunch.shape[1]))
    st.write(df_crunch)

# Payput
uploaded_file_payouts = st.sidebar.file_uploader("Upload Payouts", type=["csv"])
if uploaded_file_payouts is not None:
    df_payouts = pd.read_csv(uploaded_file_payouts)
    st.subheader("Payout Structure")
    st.write("There are %d rows and %d columns in Payout file" %(df_payouts.shape[0],df_payouts.shape[1]))
    st.write(df_payouts) 

# Names
uploaded_file_payouts = st.sidebar.file_uploader("Upload Name Mappings", type=["csv"])
if uploaded_file_payouts is not None:
    df_names = pd.read_csv(uploaded_file_payouts)
    st.subheader("Name Mappings")
    st.write("There are %d rows and %d columns in Name Mappings file" %(df_names.shape[0],df_names.shape[1]))
    st.write(df_names) 

if st.button('Run Simulation'):

    ## Creating player statistics database
    player_info_database = {}
    for player in df_fd.iterrows():
        name = player[1]["Name"].lower()
        projection = player[1]["Projection"]
        std_dev = player[1]["Std Dev"]
        ownership = player[1]["Ownership%"] / 100
        player_info_database[name] = {"projection": projection, "std":std_dev, "ownership": ownership}
        
    df_players = pd.DataFrame(player_info_database).T

    ## Creating lineup statistics
    lineups_database = []
    lineup_number = 1
    for lineup in df_crunch.iterrows():
        players = list(lineup[1].values)
        lineup_names = list(lineup[1].apply(lambda x: x.split(":")[1].lower()).values)
        data = {"lineup": lineup_number, "player_names": lineup_names, "players": players}
        lineups_database.append(data)
        lineup_number = lineup_number + 1 


    ## Resolve name mismatching
    lineup_players = find_players_lineups(lineups_database)

    for name in lineup_players:
        ## Already information available in the player_info_db
        if name in player_info_database:
            pass
        else:
            potential_players = find_player_in_the_mapping_table(df_names, name)
            found = False
            for player in potential_players:
                if player in player_info_database:
                    player_info_database[name] = player_info_database[player]
                    found = True
            if not found:
                st.write(name, " not found")
                st.write("Potential mappings that you can put in the mappings file")
                candidates = find_potential_matches(player_info_database, name, 3)
                for c in candidates:
                    st.write(name, " --> ", c)
              
    ## Find the total ownership
    for i in range(len(lineups_database)):
        prod_ownership = float(1)
        for name in lineups_database[i]["player_names"]:
            prod_ownership *= player_info_database[name]["ownership"] 
        lineups_database[i]["prod_ownership"] = prod_ownership



    ## Normalize ownership
    total_ownerhip = np.sum([i["prod_ownership"] for i in lineups_database])
    for i in range(len(lineups_database)):
        lineups_database[i]["norm_prod_ownership"] =  lineups_database[i]["prod_ownership"] / total_ownerhip
        lineups_database[i]["duplication"] = lineups_database[i]["norm_prod_ownership"] * total_entries


    ## Create lineup statistics database
    df_result = pd.DataFrame()
    df_result["lineup number"] = [lineup["lineup"] for lineup in lineups_database]
    df_result["prod ownership"] = [lineup["prod_ownership"] for lineup in lineups_database]
    df_result["norm prod ownership"] = [lineup["norm_prod_ownership"] for lineup in lineups_database]
    df_result["duplication"] = [lineup["duplication"] for lineup in lineups_database]


    st.subheader("Lineup statistics")
    st.write(df_result.style.format({"prod ownership" :"{:.9f}", "norm prod ownership": "{:.7f}", "duplication": "{:.7f}"}))



    ## Payput dictionary
    pay_out = dict(zip(df_payouts.iloc[:,0], df_payouts.iloc[:,1]))


    ## Run the simulation
    with st.spinner('Running the simulation'):        
        num_lineups = len(lineups_database)
        r = np.zeros((num_lineups,number_sims))
        for line in range(num_lineups):
            sims = np.zeros(number_sims)
            players = lineups_database[line]["player_names"]
            for player in players:
                proj = player_info_database[player]["projection"]
                sd = player_info_database[player]["std"]
                sim = normal(loc=proj, scale=sd, size = number_sims)
                sims += sim
            r[line] = sims

        df_sims = pd.DataFrame(r)

        df_sims.columns = ["Sim " + str(i) for i in range(1, number_sims + 1)]

        
        if display == "Yes":
            st.subheader("Simulations")
            st.write(df_sims)

        st.success('Successfully Ran the Simulations')


        ## Ranking the simulation
        df_sims_ranks = df_sims.rank(axis=0, ascending= False, method="min").apply(np.int64)

        if display == "Yes":
            st.subheader("Ranked Simulations")
            st.write(df_sims_ranks)
            
        st.success('Successfully Ranked the Simulations')

        ## Line up duplication
        df_duplications = pd.DataFrame([(l["lineup"],l["duplication"]) for l in lineups_database],
         columns=["lineup", "duplication"])

        df_duplications = df_result[["lineup number", "duplication"]]


        ## Prize for each lineup in each simulation
        df_price_money = pd.DataFrame()
        for c in df_sims_ranks.columns:
            df_price_money[c] = df_sims_ranks[c].apply(lambda x: (pay_out[x]) ) 

        ## Divide the prize money by duplication
        df_final_result = df_price_money.sum(axis = 1) / df_duplications["duplication"]
        df_final_result = df_final_result.sort_values(ascending=False)

        sims_lineups = [i + 1 for i in list(df_final_result.index)]
        score_lineups = list(df_final_result.values)

        final_result = []
        for i, lineup in enumerate(sims_lineups):
            final_result.append((lineup, ",".join(lineups_database[lineup - 1]["players"]), score_lineups[i]))

        df_final_result = pd.DataFrame(final_result)
        df_final_result.columns = ["lineups", "Sim Players", "Expected Money"]
        df_final_result["Expected Money"] = df_final_result["Expected Money"] / number_sims

        df_final_result_downloads = df_final_result["Sim Players"].apply(lambda x: pd.Series(str(x).split(",")))
        player_columns = ["Player " +  str(i + 1) for i in list(df_final_result_downloads.columns)]
        df_final_result_downloads.columns = player_columns

        df_final_result_downloads["lineups"] = df_final_result["lineups"]
        df_final_result_downloads["Expected Money"] = df_final_result["Expected Money"]


        if display == "Yes":
            st.subheader("Ranked SIM Lineups")
            st.write(df_final_result_downloads)

        st.success('Successfully Ranked the Prize/duplication Lineups')
        ## Save the ranked simulation file
        csv = convert_df(df_final_result_downloads)
        st.download_button(
            label="Download Ranked Lineups",
            data=csv,
            file_name='sim_rankings.csv',
            mime='text/csv',
        )

