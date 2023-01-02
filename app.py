import streamlit as st
import numpy as np
import pickle
import pandas as pd 
import logging
from gensim.models import TfidfModel
from nltk.corpus import stopwords
from nltk import download
from gensim.similarities import SparseTermSimilarityMatrix, WordEmbeddingSimilarityIndex
import gensim.downloader as api
import pickle 
from gensim.corpora import Dictionary
from tqdm import tqdm


# ['Title', 'Type', 'Sector','Key words', 'Problem/Opportunity', 
#           'Description', 'Added Value','Impact']

columns = ["Key words","Title","Description"]


path = "./dependencies/"


logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


# Import and download stopwords from NLTK.




def file_path(column, variable_name, path=path):
    return path+"".join(column.split())+"_"+variable_name+".pickle"


df = pd.read_excel('./Example of the original database (1).xlsx')
df = df.iloc[:, :11]


@st.cache(persist=True)
def load_api():
    download('stopwords')  # Download stopwords list.
    stop_words = stopwords.words('english')
    portuguese = stopwords.words('portuguese')
    stop_words.extend(portuguese)
    model =  api.load('word2vec-google-news-300')
    return model , stop_words


model, stop_words = load_api()



def preprocess(sentence,stop_words=stop_words):
    sentence = str(sentence)
    return [w for w in sentence.lower().split() if w not in stop_words]

def save_variable(column,variable_name,variable): 
    p = file_path(column,variable_name,path = path)
    with open(p,"wb") as f :
        pickle.dump(variable,f)
        
        
def createtheAI(column,model=model):
    sentences = df[column].values
    processed_sentences = []
    for sentence in sentences : 
        processed_sentences.append(preprocess(sentence))
    # Define dictionary and create bag of words
    dictionary = Dictionary(processed_sentences)
    bow = [dictionary.doc2bow(sentence) for sentence in processed_sentences]
    # Creating the Term Frequency - Inverse Document Frequency
    tfidf = TfidfModel(bow)
    tfidf_sentences = [tfidf[sentence] for sentence in bow]
    # Term Indexing and Similarity Matrix
    termsim_index = WordEmbeddingSimilarityIndex(model)
    termsim_matrix = SparseTermSimilarityMatrix(termsim_index, dictionary, tfidf)
    # Saving the envirenmental variables
    save_variable(column, "termsim_matrix", termsim_matrix)
    save_variable(column,"tfidf",tfidf)
    save_variable(column,"dictionary",dictionary)

# loads variables 
def load_variables(column):
    l = ["termsim_matrix","tfidf","dictionary"]
    paths = []
    for variable_name in l :
        paths.append(file_path(column, variable_name))
    with open(paths[0],"rb") as f :
        termsim_matrix = pickle.load(f)
    with open(paths[1],"rb") as f :
        tfidf = pickle.load(f)
    with open(paths[2],"rb") as f :
        dictionary = pickle.load(f)
        
    return termsim_matrix, tfidf, dictionary

# preprocessing the input
def prepare_input(s, dictionary, tfidf):
    precessed_input = preprocess(s)
    bow_input = dictionary.doc2bow(precessed_input)
    tfidf_input = tfidf[bow_input]
    return tfidf_input


def calculate_similarity(s1, s2, column):
    termsim_matrix, tfidf, dictionary = load_variables("Title")
    in1 = prepare_input(s1, dictionary, tfidf)
    in2 = prepare_input(s2, dictionary, tfidf)
    similarity = termsim_matrix.inner_product(
        in1, in2, normalized=(True, True))
    return similarity


def similarity_between_two_rows(idx1, idx2, available_columns=columns):
    sim = 0
    for column in available_columns:
        s1 = df.loc[idx1, column]
        s2 = df.loc[idx2, column]
        sim += calculate_similarity(s1, s2, column)
    sim = sim/len(available_columns)
    return sim

def update_sim_dic(columns):
    n = len(df)
    d = {}
    for i in tqdm(range(0,n-1)):
        for j in range(i+1,n):
            s = similarity_between_two_rows(i,j,columns)
            d[f"{i},{j}"] = s
    with open(path+'d.pickle','wb') as f : 
        pickle.dump(d,f)


# loads variables
def load_variables(column):
    l = ["termsim_matrix", "tfidf", "dictionary"]
    paths = []
    for variable_name in l:
        paths.append(file_path(column, variable_name))
    with open(paths[0], "rb") as f:
        termsim_matrix = pickle.load(f)
    with open(paths[1], "rb") as f:
        tfidf = pickle.load(f)
    with open(paths[2], "rb") as f:
        dictionary = pickle.load(f)

    return termsim_matrix, tfidf, dictionary

# preprocessing the input


def prepare_input(s, dictionary, tfidf):
    precessed_input = preprocess(s)
    bow_input = dictionary.doc2bow(precessed_input)
    tfidf_input = tfidf[bow_input]
    return tfidf_input


def calculate_similarity(s1, s2, column):
    termsim_matrix, tfidf, dictionary = load_variables(column)
    in1 = prepare_input(s1, dictionary, tfidf)
    in2 = prepare_input(s2, dictionary, tfidf)
    similarity = termsim_matrix.inner_product(
        in1, in2, normalized=(True, True))
    return similarity


def similarity_between_two_rows(idx1, idx2, available_columns=columns):
    sim = 0
    for column in available_columns:
        s1 = df.loc[idx1, column]
        s2 = df.loc[idx2, column]
        sim += calculate_similarity(s1, s2, column)
    sim = sim/len(available_columns)
    return sim

# loads the dictionary that contains the similarity coefficients
def load_sim_dictionary():
    with open(path+'d.pickle','rb') as f : 
        d = pickle.load(f)
    return d

# Outputs keys for the similar ideas
def similar_ideas(thresh=0.1):
    d = load_sim_dictionary()
    v = list(d.values())
    k = list(d.keys())
    l = []
    for i in range(len(v)): 
        if v[i] > thresh : 
            l.append(k[i])
    return l 


# Outputs the names of the users that have similar ideas
def users_with_sim_ideas(thresh):
    l = similar_ideas(thresh)
    names = []
    for i in l :
        tmp = [] 
        indexes = i.split(',')
        emp1 = df.loc[int(indexes[0]),'Employee Name']
        emp2 = df.loc[int(indexes[1]),'Employee Name']
        tmp = [emp1,emp2]
        names.append(tmp)
    return names     

def TrainTheAi(columns):
    for i in columns:
        # Calling the function to create the AI here
        # All variables are saved in the dependencies folder
        createtheAI(i)
        

### streamlit 


st.title('idea matcher')

#columns
st.set_option('deprecation.showfileUploaderEncoding', False)
columns = st.multiselect(
    'What columns are you going to use ?',
    ['Title', 'Type', 'Sector','Key words', 'Problem/Opportunity', 
          'Description', 'Added Value','Impact'],
    ["Key words", "Title", "Description"])

st.write('You selected:', columns)

#button to train
if st.button("update the AI"):
    st.text('updating the AI ...')
    TrainTheAi(columns)

if st.button("update the similarity dictionary"):
    st.text('updating the similarity dictionary ...')
    update_sim_dic(columns)
    d = load_sim_dictionary()
    k = list(d.keys())
    v = list(d.values())
    m = max(v)
    idx = v.index(m)
    max_combination = k[idx]
    st.text(f"""
    maximum similarity coeff is {m:.4} 
    which can be found when comaparing the lines { max_combination } of the dataset""")

Thresh = st.number_input('Insert maximum similarity coeff')
st.write('The current number is ', Thresh)

if st.button(f'show users with sim ideas with similarity coeff > {str(Thresh)}'):
    names = users_with_sim_ideas(Thresh)
    st.write(names)