import streamlit as st
import pandas as pd
st.set_page_config(layout="wide")
# Sample Data
# data = {
#     'Store A': {'Apples': True, 'Bananas': True, 'Carrots': False},
#     'Store B': {'Apples': False, 'Bananas': True, 'Carrots': True},
#     'Store C': {'Apples': True, 'Bananas': False, 'Carrots': True},
# }

# df = pd.DataFrame(data).T  # Stores as rows
df = pd.read_json('https://github.com/jessejcarter/mypinballmap/raw/refs/heads/main/ranked.json')

# Function to style the DataFrame
def style_table(df):
    return df.style.map(lambda x: 'background-color: lightgreen' if x else 'background-color: lightcoral')

st.title("Pinball Availability Checker")

# Styled table display
st.write("### Pinball Availability Overview")
st.dataframe(style_table(df), height=int(650/18.*(df.index.size+1))+1, use_container_width=True)  # naive scaling ratio
# st.table(style_table(df))  # best fit, bad formatting

# Location selection
st.subheader("Filter by Location or Machine")
machine_selected = st.selectbox("Select a machine", df.index)
st.write(f"{machine_selected} available at:")
for location in df.loc[machine_selected][df.loc[machine_selected]].index.tolist():
    st.markdown(f" - {location}")
# st.write('\n'.join(df.loc[machine_selected][df.loc[machine_selected]].index.tolist()))

# Multi-item selection
items_selected = st.multiselect("Select one or more machines", df.index.tolist())
if items_selected:
    filtered_locations = df.columns[df.loc[items_selected].all().tolist()]
    st.write("Locations that have all selected machines:")
    for location in filtered_locations.values:
        st.markdown(f" - {location}")

# Display changelog
# read in log file and display all changes, newest first
logdf = pd.read_csv('https://github.com/jessejcarter/mypinballmap/raw/refs/heads/main/changelog.csv', names=['date','category','location','machines']).iloc[::-1]
import ast
for i in logdf.index.values:
    row = logdf.iloc[i]
    machines = ast.literal_eval(row['machines'])
    for machine in machines:
        print(f"date: {row['date']} category: {row['category']} location: {row['location']} machine: {machine}")

category_colors = {
    "add_location": "lightblue",
    "add_machine": "lightgreen",
    "remove_machine": "salmon",
    "remove_location": "salmon"
}
category_descriptions = {
    "add_location": "New location added",
    "add_machine": "New machine added",
    "remove_machine": "Machine removed",
    "remove_location": "Location removed"
}

st.subheader("📜 Change Log (Latest Updates)")

if logdf.empty:
    st.info("No changes recorded yet.")
else:
    for _, row in logdf.iloc[0:200].iterrows():  # only show last 200 events
        # set up block
        category = row["category"]
        color = category_colors.get(category, "gray")
        markdown_string = f"<div style='background-color: {color}; padding: 10px; border-radius: 5px; margin-bottom: 5px;'>"
        markdown_string += f"<b>{row['date']}</b> - <b>{category_descriptions[category]}</b>"
        machines = ast.literal_eval(row['machines'])

        # text description depends on category
        if 'machine' in category:
            for machine in machines:    
                if category == 'add_machine':
                    s = 'added at'
                else:
                    s = 'removed from'
                markdown_string += f"<br>{machine} {s} {row['location']}"
            
            
        elif 'location' in category:
            if category == 'add_location':
                for machine in machines:
                    markdown_string += f"<br>New location added: {row['location']} which has {machine}"
            else:
                markdown_string += f"<br>{row['location']} no longer tracked, had machines: {', '.join(machines)}"
        else:
            markdown_string += f"unknown event {row}"

        # finish up
        markdown_string += "</div>"
        st.markdown(markdown_string, unsafe_allow_html=True)
                # <br>{machine}</div>",
                