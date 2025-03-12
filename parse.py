import requests
from pprint import pprint

def get_all_locations_in_region(region):
    url = f'https://pinballmap.com/api/v1/region/{region}/locations.json'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        locations = response.json()
        
        if len(locations) > 1:
            raise ValueError(f'unknown key in response.json(), keys: {locations.keys()}')
        return locations['locations']
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return []

def get_distance_in_miles(lat, long, mycoords=(40.380119, -80.044823)):
    from geopy.distance import geodesic
    coord1 = (lat, long)
    return geodesic(coord1, mycoords).miles

def get_distance_to_location(loc):
    for location in locations:
        if location['name'] == loc or location['id'] == loc:
            return get_distance_in_miles(location['lat'], location['lon'])

def get_machine_data():
    url = f'https://pinballmap.com/api/v1/machines.json'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        machines = response.json()
        if len(machines) > 1:
            raise ValueError(f'unknown key in machines.json(), keys: {machines.keys()}')
        return machines['machines']
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return []

def get_machines_where_name_contains(s):    
    machine_list = list()
    for machine in machine_data:
        if s in machine['name'].lower():
            machine_list.append(machine)
            pprint(f"{machine['name']} id: {machine['id']} group id: {machine['machine_group_id']}")
    return machine_list

def get_probable_group_id_where_name_contains(s):
    machines = get_machines_where_name_contains(s)
    # pprint(machines)
    ids = [machine['machine_group_id'] for machine in machines]
    return max(set(ids), key=ids.count)    

def get_location_id(name):
    for location in locations:
        if name.lower() in location['name'].lower():
            return location['id']

def get_location_name(id):
    for location in locations:
        if id == location['id']:
            return location['name']

def remove_delimited_text(s, start='(', end=')'):
    import re
    pattern = re.escape(start) + r'.*?' + re.escape(end)
    return re.sub(pattern, '', s)

def get_machine_by_group_id(group_id):
    for machine in machine_data:
        if machine['machine_group_id'] == group_id:
            return machine

def get_machine_by_id(id):
    for machine in machine_data:
        if machine['id'] == id:
            return machine

def get_locations_with_machine_group_id(id):
    locations_list = list()
    for loc in locations:
        for xref in loc['location_machine_xrefs']:
            machine = xref['machine']
            if machine['machine_group_id'] == id:
                locations_list.append(loc)
                break
    return locations_list

def get_locations_with_machine_id(id):
    locations_list = list()
    for loc in locations:
        for xref in loc['location_machine_xrefs']:
            machine = xref['machine']
            if machine['id'] == id:
                locations_list.append(loc)
                break
    return locations_list


if __name__ == '__main__':
    # get all locations in Pittsburgh
    print('fetching Pittsburgh locations...')
    locations = get_all_locations_in_region('Pittsburgh')
    print(f'Found {len(locations)} locations')

    # get location ids for RBS tournament locations
    print('parsing tournament locations...')
    tournament_locations = ['Lawrence Hall','Highline','Rival']
    tournament_location_ids = list()    
    for tloc in tournament_locations:
        id = get_location_id(tloc)
        name = get_location_name(id)
        tournament_location_ids.append(id)
        print(f"found {name}, id: {id}, distance: {get_distance_to_location(id):.1f} miles")
        
    # get machine data for ALL machines
    print('fetching ALL machine data...')
    machine_data = get_machine_data()

    # get machine group ids for all machines at tournament locations
    # machine group id is a way to identify several varients (Pro, Premium, ...) with one id
    print('processing tournament machines...')
    machine_group_ids = list()
    location_dict = {loc['id']:loc for loc in locations}
    for id in tournament_location_ids:
        loc = location_dict[id]
        print(loc['name'])
        for xref in loc['location_machine_xrefs']:
            machine = xref['machine']
            # print(machine)
            machine_group_ids.append(machine['machine_group_id'])
            print(f"  {machine['name']}")
            # pprint(loc)
        print()

    # some extra machines I'm interested in
    extra_machines = ['sword of rage','madness','attack from mars','tales of the arabian']

    # get ids for all machines identified above
    print('processing additional interesting machines...')
    machine_ids = list()
    for name in extra_machines:
        group_id = get_probable_group_id_where_name_contains(name)
        if group_id:
            machine_group_ids.append(group_id)
        else:  # some older machines do not have group id, so just go off name and hope there is only one match
            machines = get_machines_where_name_contains(name)
            if len(machines) != 1:
                print('could not get a single machine for name:',name,'matches:',machines)
                continue
            machine_ids.append(machines[0]['id'])

    print('machine group ids:')
    print(machine_group_ids)
    print('machine ids (no group):')
    print(machine_ids)

    # start keeping track of which machines are at what locations
    machine_location_dict = dict()

    # loop over machine groups and get local locations which have each machine
    print('looking for local locations which have each machine group id...')
    for id in machine_group_ids:
        name = remove_delimited_text(get_machine_by_group_id(id)['name']).strip()
        if name not in machine_location_dict.keys():
            machine_location_dict[name] = list()
        print(name)
        for loc in get_locations_with_machine_group_id(id):
            miles = get_distance_in_miles(loc['lat'],loc['lon'])
            if miles > 15:
                continue
            print(f"  {loc['name']} ({miles:.0f} miles)")
            machine_location_dict[name].append(loc['id'])

    # again for machines without group id
    print('looking for local locations which have each machine id...')
    for id in machine_ids:
        name = get_machine_by_id(id)['name'].strip()
        if name not in machine_location_dict.keys():
            machine_location_dict[name] = list()
        print(name)
        for loc in get_locations_with_machine_id(id):
            miles = get_distance_in_miles(loc['lat'],loc['lon'])
            if miles > 15:
                continue
            print(f"  {loc['name']} ({miles:.0f} miles)")
            machine_location_dict[name].append(loc['id'])

    print('machines and locations:')
    pprint(machine_location_dict)

    # compute True/False for each machine/location combination store into a pandas DataFrame
    all_locations = sorted(set(locid for locs in machine_location_dict.values() for locid in locs))

    import pandas as pd
    new_df = pd.DataFrame(
        {loc: [loc in locs for locs in machine_location_dict.values()] for loc in all_locations},
        index=machine_location_dict.keys()
    )
    # new_df.to_json('new_data.json')
    print('all combinations:')
    print(new_df.rename(columns={col:get_location_name(col) for col in new_df.columns}))  # show location names instead of ids for printing/debugging

    # generate location rankings to show only most promising locations
    ratings = pd.Series(index=new_df.columns)

    for col in new_df.columns:
        found_loc = False
        for location in locations:
            if location['id'] == col:
                found_loc = True
                distance = get_distance_in_miles(location['lat'],location['lon'])
                break
        if not found_loc:
            print('*** could not find location', col)

        machines = list(new_df[col].index[new_df[col].values])
        num_machines = len(machines)
        rating = num_machines/distance
        ratings.loc[col] = rating

        print(f"id: {col}, name: {get_location_name(col)} distance: {distance:.1f} miles, machines: {num_machines}, rating: {rating:.2f}")
        for machine in machines:
            print('  ',machine)
    # print(ratings.sort_values())

    ranked_df = new_df[ratings[ratings>0.5].sort_values(ascending=False).index]
    ranked_df_with_names = ranked_df.rename(columns={col:get_location_name(col) for col in ranked_df.columns})
    print('locations arbitrarily ranked:')
    print(ranked_df_with_names)
    ranked_df_with_names.to_json('ranked.json', indent=2)

    # import sys
    # sys.exit(0)

    # some fake data to show differences
    # new_df['foo'] = False
    # new_df.loc['Deadpool','foo'] = True
    # new_df.loc['John Wick','Coop DeVille'] = False
    # new_df.loc['JAWS','Cattivo'] = True
    # new_df.loc['Jurassic Park','Cattivo'] = True
    # new_df.drop(columns='Tiki Lounge', inplace=True)
    # print(new_df)

    # load old data to look for differences
    # df = pd.read_json('2025-03-05.json')  # eventually "old_data.json"
    df = pd.read_json('old_data.json')

    # **Find store changes BEFORE aligning**
    old_stores = set(df.columns)
    new_stores = set(new_df.columns)

    added_stores = new_stores - old_stores
    removed_stores = old_stores - new_stores
    # print('added stores:', added_stores)
    # print('removed stores:', removed_stores)

    # **Align DataFrames (ensuring same structure)**
    df_old, df_new = df.align(new_df, fill_value=False)

    # **Find availability changes**
    changes = df_old != df_new

    # **Generate text-based differences**
    change_log = list()
    from datetime import datetime
    date_string = datetime.now().strftime("%Y-%m-%d")

    # Report new stores
    for store in added_stores:
        store_name = get_location_name(store)
        items_at_new_store = df_new.index[df_new[store]].tolist()
        change_log.append({"date":date_string, "category":"add_location", "location":store_name, "machines":items_at_new_store})
        for item in items_at_new_store:
            print(f"A new location {store_name} is being tracked which has {item}.")

    # Report removed stores
    for store in removed_stores:
        store_name = get_location_name(store)
        items_at_old_store = df_old.index[df_old[store]].tolist()
        print(f"Location {store_name} is no longer tracked, which had: {', '.join(items_at_old_store)}.")
        change_log.append({"date":date_string, "category":"remove_location", "location":store_name, "machines":items_at_old_store})

    # process individual machine changes
    import numpy as np
    coord = np.where(changes)

    # print('processing individual machine changes...')
    for machine, location in [(df_new.index[x],df_new.columns[y]) for x, y in zip(coord[0], coord[1])]:
        # print((machine, location))
        if location in added_stores or location in removed_stores:
            # print('  already handled', location)
            continue
        if df_new.at[machine, location]:  # Now available
            store_name = get_location_name(location)
            print(f"{machine} is now available at {store_name}.")
            change_log.append({"date":date_string, "category":"add_machine", "location":store_name, "machines":[machine]})
        else:
            store_name = get_location_name(location)
            print(f"{machine} is no longer available at {store_name}.")
            change_log.append({"date":date_string, "category":"remove_machine", "location":store_name, "machines":[machine]})
            
    # **Print results**
    # for change in changes_text:
    #     print(change)
    print()
    print('change log:')
    pprint(change_log)

    # save changes as a DataFrame so we can export to CSV, append to previous changes
    if len(change_log) > 0:
        print(pd.DataFrame(change_log))
        pd.DataFrame(change_log).to_csv('changelog.csv',index=False,header=False, mode='a')

    # new data now becomes old
    new_df.to_json('old_data.json', indent=2)
