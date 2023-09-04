import streamlit as st
import pandas as pd
import numpy as np
import math
from keras.models import Model
from keras.layers import Input, Dense, Flatten
from keras.applications.resnet50 import ResNet50, preprocess_input
import cv2
import sqlite3
from urllib.request import Request, urlopen
import json
import itertools
import os
import requests


# Define the callback function outside of the class
def draw_function(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDBLCLK:
        global b, g, r, xpos, ypos, clicked
        clicked = True
        xpos = x
        ypos = y
        b, g, r = param[y, x]
        b = int(b)
        g = int(g)
        r = int(r)

def is_url_image(image_url):
    if (image_url[:4].lower() == 'http' or image_url[:3].lower() == 'www'):
        image_formats = ("image/png", "image/jpeg", "image/jpg")
        r = requests.head(image_url)
        if r.headers["content-type"] in image_formats:
            return True
    return False

def catch_wrong_url_image():
    st.error('Please provide a correct URL path of a photo', icon="🚨")
    with st.expander("See help"):
        st.markdown('''
                    If you want to enter a photo URL path, you can follow the instructions below:
                    
                    1. Right-click on the selected article image.
                    2. Select the option `Copy image address`, as shown on the image below.
                    3. (Optional) Paste the copied URL path on a new tab and press `Enter` key to check that is the correct image.
                    4. Paste the copied URL path on the text input area above.
                ''')
        st.image("../data/copy_image_address.jpg", use_column_width='auto')    

def delete_article():
    ward = Wardrobe()
    img = ward.get_image_path_of_article_with_id(selected_id)
    ward.delete_article_with_id(selected_id)
    # Remove respective uploaded file from folder
    if img.startswith('streamlit_uploaded_photos'):
        os.remove(img)
    st.success(f"Article with ID {selected_id} has been deleted from the Wardrobe.", icon="✅")

def update_table(id, column, new_value):
    ward = Wardrobe()
    ward.update_column_value_of_article_with_id(id, column, new_value)
    st.success(f"Article with ID {id} has been updated.", icon="✅")

def new_article_form(image_output, colour):
    ward = Wardrobe()
    with st.form("new_article_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            # Update Article's Category value
            current_category = category_values.index(image_output.subCategory[0])
            selected_category = st.selectbox('Select Category:', category_values, index=current_category)
            # Update Article's Type value
            current_type = type_values.index(image_output.articleType[0])
            selected_type = st.selectbox('Select Type:', type_values, index=current_type)
        with col2:
            # Update Article's Gender/Age Group
            current_gender = gender_values.index(image_output.gender[0])
            selected_gender = st.selectbox('Select Gender/Age Group:', gender_values, index=current_gender)
            # Update Article's baseColour
            current_colour = colour_values.index(colour)
            selected_colour = st.selectbox('Select Base Colour:', colour_values, index=current_colour)
        with col3:
            # Update Article's Season
            current_season = season_values.index(image_output.season[0])
            selected_season = st.selectbox('Select Season:', season_values, index=current_season)
            # Update Article's Usage
            current_usage = usage_values.index(image_output.usage[0])
            selected_usage = st.selectbox('Select Usage:', usage_values, index=current_usage)                            
        submitButton = st.form_submit_button("Update Article Values And Create Combinations")
        if submitButton:
            image_output.subCategory[0] = selected_category
            image_output.articleType[0] = selected_type
            image_output.gender[0] = selected_gender
            image_output.baseColour[0] = selected_colour
            image_output.season[0] = selected_season
            image_output.usage[0] = selected_usage
            st.success("Article has been updated.", icon="✅")
            '###### Combinations Table'
            combinations = pd.DataFrame(ward.create_combinations_of_article_with_wardrobe_clothes(image_output),
                                        columns=['Category','Article','Gender_Age_Group','Base_Colour','Season','Usage',
                                                    'Image_path', 'ID_match','Category_match', 'Article_match', 
                                                    'Gender_Age_Group_match', 'Base_Colour_match', 'Season_match', 'Usage_match', 
                                                    'Image_path_match'])
            st.dataframe(combinations, hide_index=True)
            for i, row in combinations.iterrows():
                f'###### Combination {i+1}'
                if combinations.subCategory[i] == 'Topwear':
                    st.image(combinations.image_path[i], use_column_width='auto', channels='BGR')
                    st.image(combinations.image_path_match[i], use_column_width='auto', channels='BGR')
                else:
                    st.image(combinations.image_path_match[i], use_column_width='auto', channels='BGR')
                    st.image(combinations.image_path[i], use_column_width='auto', channels='BGR')

def update_new_article(selected_category,selected_type,selected_gender,selected_colour,selected_season,selected_usage):
    image_output.subCategory[0] = selected_category
    image_output.articleType[0] = selected_type
    image_output.gender[0] = selected_gender
    image_output.baseColour[0] = selected_colour
    image_output.season[0] = selected_season
    image_output.usage[0] = selected_usage
    st.success("Article has been updated.", icon="✅")
    st.session_state["text"] = ""

def insert_article(path):
    ward = Wardrobe()
    # Display photo if path is provided
    if path not in ward.get_existing_image_paths():
        ward.insert_article_to_wardrobe_from_image_path(path)
        st.success("Article was inserted in the Wardrobe.", icon="✅")
    else:
        st.error('Article Image already exists in the Wardrobe.', icon="🚨")
    st.session_state["text"] = ""

def insert_articles(image_list):
    for image_file in image_list:
        if image_file is not None:
            # file_details = {"FileName":image_file.name,"FileType":image_file.type}
            st.image(image_file)
            f = open(os.path.join("streamlit_uploaded_photos",image_file.name), "wb")
            f.write(image_file.getbuffer())
            path = 'streamlit_uploaded_photos/' + image_file.name
            insert_article(path)
    st.session_state["file_uploader_key"] += 1

def delete_wardrobe():
    ward = Wardrobe()
    ward.delete_wardrobe()
    folder_path = 'streamlit_uploaded_photos/'
    # Verify if the folder exists
    if os.path.exists(folder_path):
        # Get a list of all files in the folder
        files = os.listdir(folder_path)
        # Loop through the files and delete each one
        for file in files:
            file_path = os.path.join(folder_path, file)
            # Check if it's a file (not a subdirectory)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {str(e)}")


class Wardrobe:

    # Constructor for the Wardrobe class and creation of the wardrobe table
    def __init__(self):
        # This connection will be used to interact with the SQLite database
        self.conn = sqlite3.connect('my_dressmeup_wardrobe.db')
        # Create a dictionary with the compatible colors
        self.color_compatibility_rules, self.colors_df = self.create_color_combatibility_rules()
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Create the 'wardrobe' table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS wardrobe (id INTEGER PRIMARY KEY AUTOINCREMENT, \
                subCategory TEXT, articleType TEXT, gender TEXT, baseColour TEXT, season TEXT, \
                usage TEXT, image_path TEXT)''')
        df = pd.read_csv('../data/df.csv', sep = '\t').drop_duplicates()
        self.model = self.create_model(df)
        # Create a DataFrame to store the encoded values and their corresponding labels
        subCategory_labels = df[['subCategory_enc', 'subCategory']].drop_duplicates().\
            sort_values(by='subCategory_enc')['subCategory'].tolist()
        articleType_labels = df[['articleType_enc', 'articleType']].drop_duplicates().\
            sort_values(by='articleType_enc')['articleType'].tolist()
        gender_labels = df[['gender_enc', 'gender']].drop_duplicates().\
            sort_values(by='gender_enc')['gender'].tolist()
        baseColour_labels = df[['baseColour_enc', 'baseColour']].drop_duplicates().\
            sort_values(by='baseColour_enc')['baseColour'].tolist()
        season_labels = df[['season_enc', 'season']].drop_duplicates().\
            sort_values(by='season_enc')['season'].tolist()
        usage_labels = df[['usage_enc', 'usage']].drop_duplicates().\
            sort_values(by='usage_enc')['usage'].tolist()
        self.target_names = [subCategory_labels, articleType_labels, gender_labels,
                        baseColour_labels, season_labels, usage_labels]

    def create_model(self, df):
        weights_path = '../models/weights.85-1.77.hdf5'
        # Define image dimensions
        img_height, img_width = 224, 224
        # Use the ResNet50 pretrained model as the feature extractor
        resnet_model = ResNet50(include_top=False,
                                input_shape=(img_height, img_width, 3),
                                pooling='avg',
                                weights='imagenet')
        # Freeze the layers of the ResNet50 model to use it as a feature extractor
        for layer in resnet_model.layers:
            layer.trainable = False
        # Create the multi-output model
        inputs = Input(shape=(img_height, img_width, 3))
        x = preprocess_input(inputs)
        x = resnet_model(x)
        x = Flatten()(x)
        x = Dense(512, activation='relu')(x)
        # Define the number of classes for each output column
        num_classes_gender = len(df['gender'].unique())
        num_classes_articleType = len(df['articleType'].unique())
        num_classes_baseColour = len(df['baseColour'].unique())
        num_classes_usage = len(df['usage'].unique())
        # Output layers for each output column
        subCategory_output = Dense(1, activation='sigmoid', name='subCategory_output')(x)
        articleType_output = Dense(num_classes_articleType, activation='softmax', name='articleType_output')(x)
        gender_output = Dense(num_classes_gender, activation='softmax', name='gender_output')(x)
        baseColour_output = Dense(num_classes_baseColour, activation='softmax', name='baseColour_output')(x)
        season_output = Dense(1, activation='sigmoid', name='season_output')(x)
        usage_output = Dense(num_classes_usage, activation='softmax', name='usage_output')(x)
        # Create the model with multiple output layers
        model = Model(inputs=inputs, outputs=[subCategory_output, articleType_output, gender_output, 
                                            baseColour_output, season_output, usage_output])
        # Compile the model with appropriate loss functions for each output
        model.compile(optimizer='adam',
                    loss={'subCategory_output': 'binary_crossentropy',
                            'articleType_output': 'sparse_categorical_crossentropy',  
                            'gender_output': 'sparse_categorical_crossentropy',
                            'baseColour_output': 'sparse_categorical_crossentropy',
                            'season_output': 'binary_crossentropy',
                            'usage_output': 'sparse_categorical_crossentropy'},
                    metrics=['accuracy'])
        model.load_weights(weights_path)
        return model
        
    def read_image_from_path(self, path):
        if (path[:4].lower() == 'http' or path[:3].lower() == 'www'):
            request_site = Request(path, headers={"User-Agent": "Mozilla/5.0"})
            req = urlopen(request_site).read()
            arr = np.asarray(bytearray(req), dtype=np.uint8)
            img = cv2.imdecode(arr, -1)
        else:
            img = cv2.imread(path)
        return img

    def set_values_from_image_path(self, path):
        output = ["subCategory", "articleType", "gender", "baseColour", "season", "usage"]
        img = self.read_image_from_path(path)
        # Check that is an image
        
        # Transform to jpg
        _, buffer = cv2.imencode('.jpg', img)
        img = np.array(buffer).tobytes()
        nparr = np.frombuffer(img, np.byte)
        img = cv2.imdecode(nparr, cv2.IMREAD_ANYCOLOR)
        # Rescale, normalize image
        sample_image = cv2.resize(img, (224, 224))
        sample_image = np.expand_dims(sample_image, axis=0)/255.
        # Make predictions
        image_pred = self.model.predict(sample_image)
        # Create a dictionary to store the predicted classes
        output_dict = {}
        for i, y_pred_output in enumerate(image_pred):
            # Get the predicted class index
            if y_pred_output.shape[1] == 1:
                predicted_class_index = (np.squeeze(y_pred_output) >= 0.5).astype(int)
            else:
                predicted_class_index = np.argmax(y_pred_output, axis=1)[0]
            # Get the corresponding human-readable class label
            image_output_class = self.target_names[i][predicted_class_index]
#             # Print the predicted class label
#             print("The predicted class for", output[i], "is", image_output_class)
            # Store the predicted class in the dictionary
            output_dict[output[i]] = [image_output_class]
        # Create a DataFrame from the dictionary
        output_dict['image_path'] = [path]
        return pd.DataFrame(output_dict)
    
    # Function to add a garment to the Wardrobe per image
    def insert_article_to_wardrobe_from_image_path(self, path):
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Begin a transaction
        c.execute('BEGIN TRANSACTION')
        df_output = self.set_values_from_image_path(path)
        # Insert the values into the 'wardrobe' table in the database
        c.executemany('INSERT INTO wardrobe (subCategory, articleType, gender, baseColour, season, \
                      usage, image_path) VALUES (?, ?, ?, ?, ?, ?, ?)', df_output.values.tolist())
        # Commit the changes to the database
        conn.commit()

    # Function to run SELECT query on the SQLite database
    def query_wardrobe(self, query):
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Execute the SELECT query
        c.execute(query)
        # Fetch all rows from the query result
        rows = c.fetchall()
        # Return the query result
        return rows
    
    def delete_wardrobe(self):
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Define query to delete wardrobe
        c.execute('DROP TABLE wardrobe')
        # Commit changes to the database
        conn.commit()
        # Close the connection to the SQLite database
        self.conn.close()
        
    def delete_article_with_id(self, article_id):
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Define query to delete wardrobe
        c.execute('DELETE FROM wardrobe WHERE id = ?', (article_id,))
        # Commit changes to the database
        conn.commit()
        
    def get_all_clothes(self):
        # Define the SELECT query to show all user's clothes
        query = 'SELECT ID, subCategory, articleType, gender, baseColour, season, usage, image_path \
            FROM wardrobe'
        # Call the function to run the SELECT query on the database and retrieve the result
        return self.query_wardrobe(query)
        
    def get_existing_ids(self):
        # Define the SELECT query to show all existing IDs
        query = 'SELECT ID FROM wardrobe'
        # Call the function to run the SELECT query on the database and retrieve the result
        result_list = [t[0] for t in self.query_wardrobe(query)]
        return result_list
    
    def get_existing_combination_ids(self):
        # Define the SELECT query to show all existing IDs
        query = 'SELECT ID FROM combinations'
        # Call the function to run the SELECT query on the database and retrieve the result
        result_list = [t[0] for t in self.query_wardrobe(query)]
        return result_list

    def get_existing_image_paths(self):
        # Define the SELECT query to show all existing image paths
        query = 'SELECT image_path FROM wardrobe'
        # Call the function to run the SELECT query on the database and retrieve the result
        result_list = [t[0] for t in self.query_wardrobe(query)]
        return result_list
    
    def does_combinations_table_exist(self):
        # Define the SELECT query to show all existing image paths
        query = "SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='combinations'"
        result_list = [t[0] for t in self.query_wardrobe(query)]
        return result_list == 1
    
    def get_subCategory_of_article_with_id(self, article_id):
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Define query to delete wardrobe
        c.execute('SELECT subCategory FROM wardrobe WHERE id = ?', (article_id,))
        return c.fetchall()[0][0]

    def get_articleType_of_article_with_id(self, article_id):
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Define query to delete wardrobe
        c.execute('SELECT articleType FROM wardrobe WHERE id = ?', (article_id,))
        return c.fetchall()[0][0]

    def get_gender_of_article_with_id(self, article_id):
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Define query to delete wardrobe
        c.execute('SELECT gender FROM wardrobe WHERE id = ?', (article_id,))
        return c.fetchall()[0][0]

    def get_baseColour_of_article_with_id(self, article_id):
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Define query to delete wardrobe
        c.execute('SELECT baseColour FROM wardrobe WHERE id = ?', (article_id,))
        return c.fetchall()[0][0]
    
    def get_season_of_article_with_id(self, article_id):
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Define query to delete wardrobe
        c.execute('SELECT season FROM wardrobe WHERE id = ?', (article_id,))
        return c.fetchall()[0][0]    

    def get_usage_of_article_with_id(self, article_id):
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Define query to delete wardrobe
        c.execute('SELECT usage FROM wardrobe WHERE id = ?', (article_id,))
        return c.fetchall()[0][0]

    def get_image_path_of_article_with_id(self, article_id):
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Define query to delete wardrobe
        c.execute('SELECT image_path FROM wardrobe WHERE id = ?', (article_id,))
        return c.fetchall()[0][0]

    def get_article_image_path(self, article_id):
        path = self.get_image_path_of_article_with_id(article_id)
        img = self.read_image_from_path(path)
        return img

    def get_image_path_of_top_bottom_article_with_id(self, comb_id, categ):
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Define query to delete wardrobe
        c.execute(f"SELECT image_path_1 AS image_path FROM combinations WHERE id = ? AND \
                  subCategory_1 = '{categ}' UNION SELECT image_path_2 AS image_path FROM combinations \
                  WHERE id = ? AND subCategory_2 = '{categ}'", (comb_id,comb_id,))
        return c.fetchall()[0][0]

    def get_top_bottom_article_image_path(self, comb_id, categ):
        path = self.get_image_path_of_top_bottom_article_with_id(comb_id, categ)
        img = self.read_image_from_path(path)
        return img

    def resize_article_image_with_width(self, article_id, width):
        img = self.get_article_image_path(article_id)
        # plt.imshow(sample_image)
        # Change ratio
        scale_percent = width / img.shape[1]
        height = int(img.shape[0] * scale_percent)
        dim = (width, height)
        # resize image
        img = cv2.resize(img, dim)
        return img
    
    def popup_article_img(self, article_id):
        img = self.resize_article_image_with_width(article_id, 224)
        cv2.imshow('Close this image to continue', img)
        # Break the loop when user hits 'esc' key
        if cv2.waitKey() & 0xff == 27:
            quit()
    
    def update_column_value_of_article_with_id(self, article_id, column, new_value):
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Define query to update article
        query = f'UPDATE wardrobe SET {column} = ? WHERE id = ?'
        c.execute(query, (new_value, article_id))
        conn.commit()
        
    # Function to calculate minimum distance from all colors and get the most matching color
    def get_color_name(self, R, G, B, csv):
        minimum = 10000
        for i in range(len(csv)):
            # Manhattan distance
#             d = abs(R- int(csv.loc[i,"R"])) + abs(G- int(csv.loc[i,"G"])) + abs(B- int(csv.loc[i,"B"]))
            # Euclidean distance is better for measuring color distance
            d = math.sqrt((R - int(csv.loc[i,"r"]))**2 + 
                          (G - int(csv.loc[i,"g"]))**2 + 
                          (B - int(csv.loc[i,"b"]))**2)
            if(d<=minimum):
                minimum = d
                cname = csv.loc[i,"name"]
        return cname
    
    def get_color_hex(self, name):
        self.colors_df[self.colors_df['name'] == name]['hex'].item()
        return hex_value

    def get_color_value_by_clickpoint_detection_of_article_with_id(self, img):
        # Declaring global variables (are used later on)
        global clicked, b, g, r, xpos, ypos
        clicked = False
        r = g = b = xpos = ypos = 0
        window_open = False
        text = ""
        # Just try as long as a matching window is found
        while not window_open:
            try:
                cv2.namedWindow('image')
                cv2.setMouseCallback('image', draw_function, img)
                window_open = True
                while True:  # Check if the window is open            
                    cv2.imshow("image", img)
                    if (clicked):
                        cv2.rectangle(img, (20,20), (750,60), (b,g,r), -1)
                        # Creating text string to display (Color name and RGB values)
                        text = self.get_color_name(r, g, b, self.colors_df) 
                        cv2.putText(img, text, (50,50), 2, 0.8, (255,255,255), 2, cv2.LINE_AA)
                        # For very light colours we will display text in black colour
                        if(r + g + b >= 600):
                            cv2.putText(img, text,(50,50),2,0.8,(0,0,0),2,cv2.LINE_AA)
                        clicked=False
                    # Break the loop when user hits 'esc' key or closes the window
                    if (cv2.waitKey(20) & 0xFF == 27) or cv2.getWindowProperty('image', 0) < 0:
                        break
            except:
                # Destroy any "erroneous" windows OpenCV might have created
                cv2.destroyAllWindows()
        cv2.destroyAllWindows()
        return text
    
    def create_color_combatibility_rules(self):
        with open('../data/colors.json') as json_file:
            colors = json.load(json_file)
        csv_data = []
        for color in colors:
            csv_data.append([
                color['index'],
                color['name'],
                color['hex'],
                color['rgb'][0],
                color['rgb'][1],
                color['rgb'][2],
                color['cmyk'][0],
                color['cmyk'][1],
                color['cmyk'][2],
                color['cmyk'][3]
            ])
        colors_df = pd.DataFrame(csv_data, columns=['index', 'name', 'hex', 'r', 'g', 'b', 'c', 'm', 'y', 'k'])
        with open('../data/combinations.json') as json_file:
            colour_combinations = json.load(json_file)
        block_pairs = set()
        # Iterate over each value (list of IDs) in the blocking index
        for value in colour_combinations.values():
            # Use itertools.combinations to generate unique pairs within the current block
            block_pairs = block_pairs.union(set(itertools.combinations(value, 2)))
        block_pairs = {(a, b) for a, b in block_pairs if a != 0}
        color_comb_dict = {}
        for key, value in block_pairs:
            if key not in color_comb_dict:
                color_comb_dict[key] = [value]
            else:
                color_comb_dict[key].append(value)
        color_comb_dict = {key: sorted(values) for key, values in color_comb_dict.items()}
        # Create a dictionary mapping index values to names
        index_to_name = colors_df.set_index('index')['name'].to_dict()
        # Replace index values with respective names in color_comb_dict
        color_comb_names = {}
        for key, value_list in color_comb_dict.items():
            color_comb_names[index_to_name[key]] = [index_to_name[val] for val in value_list]
        # Define color  rule
        colors = ["Blue", "Black", "White", "Grey", "Green", "Red", "Navy Blue", "Purple", "Pink", 
                  "Yellow", "Brown", "Orange", "Beige","Maroon", "Cream", "Olive", "Multi", "Charcoal"]
        color_compatibility_rules = {
            'Black': colors,
            'Blue': ['Black', 'White', 'Grey', 'Green', 'Red', 'Navy Blue', 'Purple', 'Pink'],
            'White': ['Black', 'Blue', 'Grey', 'Green', 'Red', 'Navy Blue', 'Purple', 'Pink'],
            'Grey': ['Black', 'Blue', 'White', 'Green', 'Red', 'Navy Blue', 'Purple', 'Pink'],
            'Green': ['Black', 'Grey', 'Navy Blue'],
            'Red': ['Black', 'Blue', 'White', 'Grey', 'Pink', 'Maroon', 'Multi', 'Charcoal'],
            'Navy Blue': ['Black', 'Blue', 'White', 'Grey', 'Green', 'Purple', 'Multi', 'Charcoal'],
            'Purple': ['Black', 'Blue', 'White', 'Grey', 'Navy Blue', 'Pink'],
            'Pink': ['Black', 'Blue', 'White', 'Grey', 'Red', 'Purple'],
            'Yellow': ['Black', 'Brown', 'Green', 'Olive'],
            'Brown': ['Black', 'Grey', 'Pink', 'Yellow', 'Olive'],
            'Orange': ['Black', 'Brown', 'Green', 'Olive'],
            'Beige': ['Black', 'Blue', 'Grey', 'Green', 'Pink'],
            'Maroon': ['Black', 'Grey', 'Red'],
            'Cream': ['Black', 'Blue', 'White', 'Grey', 'Green', 'Pink'],
            'Olive': ['Black', 'Brown', 'Green', 'Yellow', 'Orange'],
            'Multi': ['Black', 'Blue', 'White', 'Grey', 'Green', 'Red', 'Navy Blue', 'Purple'],
            'Charcoal': ['Black', 'Red', 'Navy Blue', 'Multi']
        }
        dict_3 = {**color_comb_names, **color_compatibility_rules}
        for key, value in dict_3.items():
            if key in color_comb_names and key in color_compatibility_rules:
                dict_3[key] = set(value + color_comb_names[key])
        color_compatibility_rules = dict_3
        return color_compatibility_rules, colors_df

    # Function to check color compatibility
    def get_compatible_colors(self, color1, color2):
        return color2 in self.color_compatibility_rules.get(color1, [])
    
    def filter_merged_df(self, filtered_df):
        # Filter the merged DataFrame based on conditions
        filtered_df = filtered_df[
            # Match Bottomwear with Topwear
            (filtered_df['subCategory'] != filtered_df['subCategory_match']) &
            (
                # Match equal gender or Unisex with any other
                (filtered_df['season'] == filtered_df['season_match']) |
                (filtered_df['season'] == 'All season') |
                (filtered_df['season_match'] == 'All season')
            ) &
            (
                # Match equal gender or Unisex with any other
                (filtered_df['gender'] == filtered_df['gender_match']) |
                (filtered_df['gender'] == 'Unisex') |
                (filtered_df['gender_match'] == 'Unisex')
            )
        ]
        # Filter the dataset based on color compatibility
        return filtered_df[filtered_df.apply(lambda row: self.get_compatible_colors(row['baseColour'], 
                                                                            row['baseColour_match']), axis=1)]
    
    def create_combinations_in_wardrobe(self):
        df = pd.DataFrame(self.get_all_clothes(),
             columns=['id','subCategory', 'articleType', 'gender', 
                      'baseColour', 'season', 'usage', 'image_path'])
        # Perform inner merge on common column 'usage'
        # Initialize an empty list to store filtered combinations
        filtered_combinations = []
        # Iterate over rows to generate combinations
        for i in range(len(df)):
            for j in range(i + 1, len(df)):
                filtered_combinations.append(pd.merge(df.iloc[[i]], df.iloc[[j]], on=['usage'], 
                                                      suffixes=('', '_match')))
        # Concatenate all filtered combinations into a single DataFrame
        merged_df = pd.concat(filtered_combinations)
        filtered_df = self.filter_merged_df(merged_df)
        # Establish a connection to the SQLite database
        conn = self.conn
        c = conn.cursor()
        # Create the 'combinations' table
        c.execute('DROP TABLE IF EXISTS combinations')
        c.execute('''CREATE TABLE IF NOT EXISTS combinations (id INTEGER PRIMARY KEY AUTOINCREMENT,\
                  id_1 INTEGER, subCategory_1 TEXT, image_path_1 TEXT, \
                  id_2 INTEGER, subCategory_2 TEXT, image_path_2 TEXT)''')
        # Insert the values into the 'combinations' table in the database
        c.executemany('INSERT INTO combinations (id_1, subCategory_1, image_path_1, id_2, subCategory_2, \
                      image_path_2) VALUES (?, ?, ?, ?, ?, ?)', filtered_df[['id','subCategory','image_path',
                                                                       'id_match','subCategory_match',
                                                                        'image_path_match']].values.tolist())
        # Commit changes to the database
        conn.commit()
        
    def get_all_clothes_combinations(self):
        # Define the SELECT query to show all user's clothes
        query = 'SELECT id, id_1, id_2 FROM combinations'
        # Call the function to run the SELECT query on the database and retrieve the result
        return self.query_wardrobe(query)
    
    def create_combinations_of_article_with_wardrobe_clothes(self, image_output):
        df = pd.DataFrame(self.get_all_clothes(),
             columns=['id', 'subCategory', 'articleType', 'gender', 'baseColour', 'season', 'usage', 'image_path'])
        merged_df = pd.merge(image_output, df, on=['usage'], suffixes=('', '_match'))
        filtered_df = self.filter_merged_df(merged_df)
        return filtered_df


ward = Wardrobe()

# Streamlit app title
img = cv2.imread('../data/logo_full.png')
st.sidebar.image(img)
st.title(':green[dressmeup]')
table_data = pd.DataFrame(ward.get_all_clothes(),
    columns=['ID','Category', 'Article', 'Gender_Age_Group', 'Base_Colour', 'Season', 'Usage', 'Image_path'])
category_values = ['Bottomwear','Topwear']
type_values = ['Capris','Jackets','Jeans','Kurtas','Leggings','Patiala','Shirts',
                                'Shorts','Skirts','Sweaters','Sweatshirts','Tops','Track Pants',
                                'Trousers','Tshirts','Tunics']
gender_values = ['Boys','Girls','Men','Unisex','Women']
colour_values = ['Aconite Violet', 'Andover Green', 'Antwarp Blue', 'Apricot Orange', 'Apricot Yellow', 
                 'Artemesia Green', 'Beige', 'Benzol Green', 'Black', 'Blackish Olive', 'Blue', 
                 'Blue Violet', 'Brick Red', 'Brown', 'Buffy Citrine', 'Burnt Sienna', 'Calamine BLue', 
                 'Cameo Pink', 'Carmine', 'Carmine Red', 'Cerulian Blue', 'Charcoal', 'Cinnamon Buff', 
                 'Cinnamon Rufous', 'Citron Yellow', 'Cobalt Green', 'Coral Red', 'Corinthian Pink', 
                 'Cossack Green', 'Cotinga Purple', 'Cream', 'Cream Yellow', 'Dark Citrine', 
                 'Dark Greenish Glaucous', 'Dark Medici Blue', 'Dark Slate Purple', 'Dark Soft Violet', 
                 'Dark Tyrian Blue', 'Deep Grayish Olive', 'Deep Indigo', 'Deep Lyons Blue', 
                 'Deep Slate Green', 'Deep Slate Olive', 'Deep Violet / Plumbeous', 'Diamine Green', 
                 'Dull Blue Violet', 'Dull Violet Black', 'Dull Viridian Green', 'Dusky Green', 
                 'Dusky Madder Violet', 'Ecru', 'English Red', 'Eosine Pink', 'Etruscan Red', 
                 'Eugenia Red | A', 'Eugenia Red | B', 'Eupatorium Purple', 'Fawn', 'Fresh Color', 
                 'Glaucous Green', 'Golden Yellow', 'Grayish Lavender - A', 'Grayish Lavender - B', 
                 'Green', 'Green Blue', 'Grenadine Pink', 'Grey', "Hay's Russet", 'Helvetia Blue', 
                 'Hermosa Pink', 'Hydrangea Red', 'Indian Lake', 'Isabella Color', 'Ivory Buff', 
                 'Jasper Red', 'Khaki', 'Krongbergs Green', 'Laelia Pink', 'Lemon Yellow', 
                 'Light Brown Drab', 'Light Brownish Olive', 'Light Glaucous Blue', 'Light Grayish Olive', 
                 'Light Green Yellow', 'Light Mauve', 'Light Pinkish Cinnamon', 'Light Porcelain Green', 
                 'Lilac', 'Lincoln Green', 'Madder Brown', 'Maple', 'Maroon', 'Mars Brown Tobacco', 
                 'Mineral Gray', 'Multi', 'Naples Yellow', 'Navy Blue', 'Neutral Gray', 'Night Green', 
                 'Nile Blue', 'Ochraceous Salmon', 'Ochre Red', 'Oil Green', 'Old Rose', 'Olive', 
                 'Olive Buff', 'Olive Green', 'Olive Ocher', 'Olive Yellow', 'Olympic Blue', 'Orange', 
                 'Orange Citrine', 'Orange Rufous', 'Orange Yellow', 'Pale Burnt Lake', "Pale King's Blue", 
                 'Pale Lemon Yellow', 'Pale Raw Umber', 'Pansy Purple', 'Peach Red', 'Peacock Blue', 'Pink', 
                 'Pinkish Cinnamon', 'Pistachio Green', 'Pomegranite Purple', 'Pompeian Red', 'Purple', 
                 'Purple Drab', 'Pyrite Yellow', 'Rainette Green', 'Raw Sienna', 'Red', 'Red Orange', 
                 'Red Violet', 'Rosolanc Purple', 'Salvia Blue', 'Scarlet', 'Sea Green', 'Seashell Pink', 
                 'Sepia', 'Slate Color', 'Spectrum Red', 'Spinel Red', 'Sudan Brown', 'Sulpher Yellow', 
                 'Sulphine Yellow', 'Taupe Brown', 'Turquoise Green', 'Vandyke Brown', 'Vandyke Red', 
                 'Venice Green', 'Veronia Purple', 'Vinaceous Cinnamon', 'Vinaceous Tawny', 'Violet', 
                 'Violet Blue', 'Violet Carmine', 'Violet Red', 'Vistoris Lake', 'Warm Gray', 'White', 
                 'Yellow', 'Yellow Green', 'Yellow Ocher', 'Yellow Orange']
season_values = ['Fall/Winter','Spring/Summer','All Season']
usage_values = ['Casual','Ethnic','Formal','Sports']

view = st.sidebar.checkbox('My Wardrobe View')
insert = st.sidebar.checkbox('Insert New Articles')
manage = st.sidebar.checkbox('My Wardrobe Management')
identify = st.sidebar.checkbox('Colour Identification')
combine = st.sidebar.checkbox('Clothes Combinations')
delete = st.sidebar.checkbox('Delete My Wardrobe')

if not view and not insert and not manage and not identify and not combine and not delete:
    st.balloons()
    ''

# Sidebar option to view the SQLite table
if view:
    st.markdown('## My Wardrobe View')
    df = st.dataframe(
        table_data,
        column_config={"Image_path": st.column_config.LinkColumn(
                help="URL to view the article",
                required=True)},
        hide_index=True,
    )

# Sidebar input for photo-path
if insert:
    st.markdown('## Insert New Articles')
    photo_path = st.text_input('Enter Photo URL Path (preferred for better AI prediction quality):', 
                               key="text")
    if photo_path and is_url_image(photo_path):
        st.button('Insert the Article to the Wardrobe', on_click=insert_article, kwargs=dict(path=str(photo_path)), type="primary")
    if photo_path and not is_url_image(photo_path):
        catch_wrong_url_image()
    st.divider()
    'OR (if you have good-quality pictures...)'
    if "file_uploader_key" not in st.session_state:
        st.session_state["file_uploader_key"] = 0
    if "uploaded_files" not in st.session_state:
        st.session_state["uploaded_files"] = []
    image_list = st.file_uploader('Upload photos:', type=['png','jpg'], accept_multiple_files=True,
                                  key=st.session_state["file_uploader_key"])
    if image_list:
        st.session_state["uploaded_files"] = image_list
        st.button("Insert the Article(s) to the Wardrobe", on_click=insert_articles, args=(image_list,),
                  type="primary")

if manage:
    st.markdown('## My Wardrobe Management')
    if (len(ward.get_existing_ids()) > 0):
        # Article ID
        selected_id = st.selectbox('Select Article ID:', tuple(ward.get_existing_ids()))
        # Article's Image
        img = ward.get_article_image_path(selected_id)
        st.image(img, use_column_width='auto', channels='BGR')
        col1, col2, col3 = st.columns(3)
        with col1:
            # Update Article's Category value
            with st.form("category_form"):
                current_category = category_values.index(ward.get_subCategory_of_article_with_id(selected_id))
                selected_category = st.selectbox('Select Category:', category_values,
                                                index=current_category)
                if st.form_submit_button("Update Category"):
                    ward.update_column_value_of_article_with_id(selected_id, 'subCategory', selected_category)
                    st.success(f"Article with ID {selected_id} has been updated.", icon="✅")
            # Update Article's Type value
            with st.form("type_form"):
                current_type = type_values.index(ward.get_articleType_of_article_with_id(selected_id))
                selected_type = st.selectbox('Select Type:', type_values, 
                                            index=current_type)
                if st.form_submit_button("Update Type"):
                    ward.update_column_value_of_article_with_id(selected_id, 'articleType', selected_type)
                    st.success(f"Article with ID {selected_id} has been updated.", icon="✅")
        with col2:
            # Update Article's Gender/Age Group
            with st.form("gender_form"):
                current_gender = gender_values.index(ward.get_gender_of_article_with_id(selected_id))
                selected_gender = st.selectbox('Select Gender/Age Group:', gender_values,
                                            index=current_gender)
                if st.form_submit_button("Update Gender/Age"):
                    ward.update_column_value_of_article_with_id(selected_id, 'gender', selected_gender)
                    st.success(f"Article with ID {selected_id} has been updated.", icon="✅")
            # Update Article's baseColour
            with st.form("colour_form"):
                current_colour = colour_values.index(ward.get_baseColour_of_article_with_id(selected_id))
                selected_colour = st.selectbox('Select Base Colour:', colour_values, 
                                            index=current_colour)
                if st.form_submit_button("Update Base Colour"):
                    ward.update_column_value_of_article_with_id(selected_id, 'baseColour', selected_colour)
                    st.success(f"Article with ID {selected_id} has been updated.", icon="✅")
        with col3:
            # Update Article's Season
            with st.form("season_form"):
                current_season = season_values.index(ward.get_season_of_article_with_id(selected_id))
                selected_season = st.selectbox('Select Season:', season_values, 
                                            index=current_season)
                if st.form_submit_button("Update Season"):
                    ward.update_column_value_of_article_with_id(selected_id, 'season', selected_season)
                    st.success(f"Article with ID {selected_id} has been updated.", icon="✅")
            # Update Article's Usage
            with st.form("usage_form"):
                current_usage = usage_values.index(ward.get_usage_of_article_with_id(selected_id))
                selected_usage = st.selectbox('Select Usage:', usage_values, 
                                            index=current_usage)
                if st.form_submit_button("Update Usage"):
                    ward.update_column_value_of_article_with_id(selected_id, 'usage', selected_usage)
                    st.success(f"Article with ID {selected_id} has been updated.", icon="✅")
        # Create a button to delete the article
        st.button('Delete article from Wardrobe', on_click=delete_article, type="primary")

# Sidebar option to create a pop-up window containing a photo
if identify:
    st.markdown('## Article Colour Point Detection')
    if (len(ward.get_existing_ids()) > 0):
        # Article ID
        sel_id = st.selectbox('Select Image of Article ID:', tuple(ward.get_existing_ids()))
        # Article's Image
        img = ward.get_article_image_path(sel_id)
        st.image(img, use_column_width='auto', channels='BGR')
        det_colour = ward.get_baseColour_of_article_with_id(sel_id)
        if st.button('Identify Article Colour', type='primary'):
            # Read and resize image
            img = ward.resize_article_image_with_width(sel_id, 600)
            det_colour = ward.get_color_value_by_clickpoint_detection_of_article_with_id(img)
            st.markdown('#### This is the chosen closest color hue in our database:')
            colmn1, colmn2, _ = st.columns(3)
            with colmn1:
                st.markdown(f'###### {det_colour}')
                hex_value = ward.colors_df[ward.colors_df['name'] == det_colour]['hex'].item()
            with colmn2:
                st.color_picker('Closest color', hex_value, label_visibility='collapsed')
            st.button("Update Base Colour", on_click=update_table, 
                      kwargs=dict(id=sel_id, column='baseColour', new_value=det_colour), type="primary")

if combine:
    st.markdown('## Clothes Combinations')
    '##### *Firstly check that all Wardrobe clothes values are correct...*'
    # but1 = st.button('Create Combinations In Wardrobe', type='primary', use_container_width=True)
    tab1, tab2 = st.tabs(["My Wardrobe Combinations", "Combinations With A New Article"])
    with tab1:
        ward.create_combinations_in_wardrobe()
        combinations = pd.DataFrame(ward.get_all_clothes_combinations(), 
                                  columns=['Combination_ID', 'Article_ID_1', 'Article_ID_2'])
        comb_df = st.dataframe(combinations,
        column_config={"Image_Path_1": st.column_config.LinkColumn(
            help="URL to view the article", required=True),
            "Image_Path_2": st.column_config.LinkColumn(
            help="URL to view the article", required=True)},
        hide_index=True, use_container_width=True)
        if (len(ward.get_existing_combination_ids()) > 0):
            # Article ID
            comb_id = st.selectbox('Select Combination ID:', tuple(ward.get_existing_combination_ids()))
            # Combination's Images (first Topwear and below the Bottomwear)
            img_1 = ward.get_top_bottom_article_image_path(comb_id, 'Topwear')
            st.image(img_1, use_column_width='auto', channels='BGR')
            img_2 = ward.get_top_bottom_article_image_path(comb_id, 'Bottomwear')
            st.image(img_2, use_column_width='auto', channels='BGR')
    with tab2:
        photo_path = st.text_input('Enter Photo URL Path:', key="photo_url")
        if photo_path and is_url_image(photo_path):
            image_output = ward.set_values_from_image_path(photo_path)
            '###### Article'
            st.dataframe(image_output, hide_index=True)
            st.image(photo_path, use_column_width='auto', channels='BGR')
            # det_colour = image_output.baseColour[0]
            # st.session_state.new_article_colour = image_output.baseColour[0]
            on = st.toggle('Identify Article Colour')
            if on:
            # if st.button('Identify Article Colour'):
                # Read and resize image
                # img = ward.resize_article_image_with_width(sel_id, 600)
                img = ward.read_image_from_path(photo_path)
                width = 600
                scale_percent = width / img.shape[1]
                height = int(img.shape[0] * scale_percent)
                dim = (width, height)
                # resize image
                img = cv2.resize(img, dim)
                det_colour = ward.get_color_value_by_clickpoint_detection_of_article_with_id(img)
                if det_colour:
                    st.markdown('#### This is the chosen closest color hue in our database:')
                    colmn1, colmn2, _ = st.columns(3)
                    with colmn1:
                        st.markdown(f'###### {det_colour}')
                        hex_value = ward.colors_df[ward.colors_df['name'] == det_colour]['hex'].item()
                    with colmn2:
                        st.color_picker('Closest color', hex_value, label_visibility='collapsed')
            with st.form("new_article_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    # Update Article's Category value
                    current_category = category_values.index(image_output.subCategory[0])
                    selected_category = st.selectbox('Select Category:', category_values, index=current_category)
                    # Update Article's Type value
                    current_type = type_values.index(image_output.articleType[0])
                    selected_type = st.selectbox('Select Type:', type_values, index=current_type)
                with col2:
                    # Update Article's Gender/Age Group
                    current_gender = gender_values.index(image_output.gender[0])
                    selected_gender = st.selectbox('Select Gender/Age Group:', gender_values, index=current_gender)
                    # Update Article's baseColour
                    current_colour = colour_values.index(image_output.baseColour[0])
                    selected_colour = st.selectbox('Select Base Colour:', colour_values, index=current_colour)
                with col3:
                    # Update Article's Season
                    current_season = season_values.index(image_output.season[0])
                    selected_season = st.selectbox('Select Season:', season_values, index=current_season)
                    # Update Article's Usage
                    current_usage = usage_values.index(image_output.usage[0])
                    selected_usage = st.selectbox('Select Usage:', usage_values, index=current_usage)                            
                submitButton = st.form_submit_button("Update Article Values And Create Combinations")
                if submitButton:
                    on = False # Make this session state...
                    image_output.subCategory[0] = selected_category
                    image_output.articleType[0] = selected_type
                    image_output.gender[0] = selected_gender
                    image_output.baseColour[0] = selected_colour
                    image_output.season[0] = selected_season
                    image_output.usage[0] = selected_usage
                    st.success("Article has been updated.", icon="✅")
                    '###### Combinations Table'
                    combinations = pd.DataFrame(ward.create_combinations_of_article_with_wardrobe_clothes(image_output),
                                                # columns=['Category','Article','Gender_Age_Group','Base_Colour','Season','Usage',
                                                #             'Image_path', 'ID_match','Category_match', 'Article_match', 
                                                #             'Gender_Age_Group_match', 'Base_Colour_match', 'Season_match', 
                                                # 'Usage_match', 
                                                #             'Image_path_match']
                                                )
                    st.dataframe(combinations, hide_index=True, 
                                 column_config={"subCategory": st.column_config.Column('Category'),
                                                "articleType": st.column_config.Column('Article'),
                                                "gender": st.column_config.Column('Gender_Age_Group'),
                                                "baseColour": st.column_config.Column('Base_Colour'),
                                                "season": st.column_config.Column('Season'),
                                                "usage": st.column_config.Column('Usage'),
                                                "image_path": st.column_config.Column('Image_path')})
                    for i, row in combinations.iterrows():
                        f'###### Combination {i+1}'
                        if combinations.subCategory[i] == 'Topwear':
                            st.image(combinations.image_path[i], use_column_width='auto', channels='BGR')
                            st.image(combinations.image_path_match[i], use_column_width='auto', channels='BGR')
                        else:
                            st.image(combinations.image_path_match[i], use_column_width='auto', channels='BGR')
                            st.image(combinations.image_path[i], use_column_width='auto', channels='BGR')
                    
                # , on_click=new_article_form, args=(image_output,det_colour,))

            # with st.form("new_article_form"):
            #     col1, col2, col3 = st.columns(3)
            #     with col1:
            #         # Update Article's Category value
            #         current_category = category_values.index(image_output.subCategory[0])
            #         selected_category = st.selectbox('Select Category:', category_values, index=current_category)
            #         # Update Article's Type value
            #         current_type = type_values.index(image_output.articleType[0])
            #         selected_type = st.selectbox('Select Type:', type_values, index=current_type)
            #     with col2:
            #         # Update Article's Gender/Age Group
            #         current_gender = gender_values.index(image_output.gender[0])
            #         selected_gender = st.selectbox('Select Gender/Age Group:', gender_values, index=current_gender)
            #         # Update Article's baseColour
            #         current_colour = colour_values.index(st.session_state.new_article_colour)
            #         selected_colour = st.selectbox('Select Base Colour:', colour_values, index=current_colour)
            #     with col3:
            #         # Update Article's Season
            #         current_season = season_values.index(image_output.season[0])
            #         selected_season = st.selectbox('Select Season:', season_values, index=current_season)
            #         # Update Article's Usage
            #         current_usage = usage_values.index(image_output.usage[0])
            #         selected_usage = st.selectbox('Select Usage:', usage_values, index=current_usage)                            
            #     submitButton = st.form_submit_button("Update Article Values And Create Combinations")
            #     if submitButton:
            #         image_output.subCategory[0] = selected_category
            #         image_output.articleType[0] = selected_type
            #         image_output.gender[0] = selected_gender
            #         image_output.baseColour[0] = selected_colour
            #         image_output.season[0] = selected_season
            #         image_output.usage[0] = selected_usage
            #         st.success("Article has been updated.", icon="✅")
            #         '###### Combinations Table'
            #         combinations = pd.DataFrame(ward.create_combinations_of_article_with_wardrobe_clothes(image_output),
            #                                     columns=['Category','Article','Gender_Age_Group','Base_Colour','Season','Usage',
            #                                              'Image_path', 'ID_match','Category_match', 'Article_match', 
            #                                              'Gender_Age_Group_match', 'Base_Colour_match', 'Season_match', 
            # 'Usage_match', 
            #                                              'Image_path_match'])
            #         comb_df = st.dataframe(combinations, hide_index=True)
            #         for i, row in combinations.iterrows():
            #             f'###### Combination {i+1}'
            #             if combinations.subCategory[i] == 'Topwear':
            #                 st.image(combinations.image_path[i], use_column_width='auto', channels='BGR')
            #                 st.image(combinations.image_path_match[i], use_column_width='auto', channels='BGR')
            #             else:
            #                 st.image(combinations.image_path_match[i], use_column_width='auto', channels='BGR')
            #                 st.image(combinations.image_path[i], use_column_width='auto', channels='BGR')
        if photo_path and not is_url_image(photo_path):
            catch_wrong_url_image()    

# Sidebar option to delete the wardrobe
if delete:
    st.markdown('## Delete My Wardrobe')
    if st.button('Delete My Wardrobe', type='primary'):
        '### Are you sure that you want to delete the whole wardrobe?'
        '##### *There is no way to revert it*...'
        column1, column2, _,_,_,_ = st.columns(6)
        with column1:
            st.button('Yes', on_click=delete_wardrobe, use_container_width=True)
        with column2:
            st.button('No', use_container_width=True)
