# Importing Dependencies
import pandas as pd
from flask import Flask, render_template, redirect, make_response,request, jsonify
import os
import json
import numpy as np
from exploration.table_maker import *
import datetime as dt
from sqlalchemy.sql import func

#################################################
# Database Setup
#################################################

conn, session = create_connection(False, './exploration/')

#################################################
######################
# Create an instance of Flask
app = Flask(__name__)
######################
# Route to render index.html
@app.route("/")
def home():

    # Pull all Show names and ID's in data base.
    ids = []
    titles = []
    names = session.query(Series)
    for i in names:
        ids.append(i.tconst)
        titles.append(i.title)
    
    name_blob = {'id': ids, 'title': titles}
    return render_template("index.html", all_shows=name_blob)
#--------------------
# Route to render about.html template using csv data
@app.route("/about")
def about():

    return render_template("about.html")
#--------------------
# Route to render featured.html template using csv data
@app.route("/featured")
def finals():

    return render_template("featured.html")
#--------------------
#error handler
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)
#--------------------
@app.route("/API")
def mainapi():
    """List all available api routes."""
    return render_template("api_home.html")
#--------------------

#--------------------
@app.route("/db_test")
def dbtest():
    results = session.query(Series.title).all()
    all_names = list(np.ravel(results))
    return jsonify(all_names)
#--------------------
# API DATA CALLS START HERE!!!!!!
#--------------------
@app.route("/plotdata/all_plots/<series_tconsts>")
def all_plots(series_tconsts):

    # Should be a list of comma separated IMDB id's
    # E.g: '2861424,101178' for Rick and Morty and Ren & Stimpy 
    selected_tconsts = [int(x) for x in series_tconsts.strip(',').split(',')]

    data_blob = []
    for tconst in selected_tconsts:
        # Query the episode table
        episodes = session.query(Episode)\
            .filter(Episode.parent_tconst == tconst)\
            .all()
        
        episode_dates = []
        # Unpack the data
        for e in episodes:
            try:
                episode_dates.append(e.original_air_date.strftime('%Y-%m-%d'))
            except AttributeError:
                episode_dates.append(None)
        
        episode_avg_ratings = [e.avg_rating for e in episodes]
        episode_titles = [e.title for e in episodes]
        episode_plots = [e.plot for e in episodes]
        episode_votes = [e.number_votes for e in episodes]
        episode_seasons = [e.season for e in episodes]
        episode_episodes = [e.episode for e in episodes]

        # Calculate by season
        season_number = []
        season_votes = []
        season_rating = []
        season_episode_count = []
        for i in range(1, max(episode_seasons) + 1):
            season_rating_query = session.query(func.avg(Episode.avg_rating))\
                            .filter(Episode.parent_tconst == tconst)\
                            .filter(Episode.season==i)\
                            .first()            

            try:
                season_rating.append(float(season_rating_query[0]))
            except TypeError:
                season_rating.append(None)

            season_votes_query = session.query(func.sum(Episode.number_votes))\
                            .filter(Episode.parent_tconst == tconst)\
                            .filter(Episode.season==i)\
                            .first()

            try:
                season_votes.append(float(season_votes_query[0]))
            except TypeError:
                season_votes.append(None)

            season_episode_count_query = session.query(Episode)\
                            .filter(Episode.parent_tconst == tconst)\
                            .filter(Episode.season==i)\
                            .count()

            try:
                season_episode_count.append(season_episode_count_query)
            except TypeError:
                season_episode_count.append(None)

            season_number.append(i)

        normalized_season = []
        for i in range(len(episode_episodes)):
            try:
                season = episode_seasons[i]
                count = season_episode_count[season - 1]
                normalized_season.append(season + (episode_episodes[i] - 1) / count)
            except:
                normalized_season.append(None)

        # Query the series table    
        series = session.query(Series)\
            .filter(Series.tconst == tconst)\
            .first()

        data_blob.append({'Series': {
                                'title': series.title,
                                'number_of_seasons': series.num_seasons,
                                'series_avg_rating': series.avg_rating,
                                'series_votes': series.num_votes,
                                'season_number': season_number,
                                'season_votes': season_votes,
                                'season_avg_rating': season_rating,
                                'season_episode_count': season_episode_count},
                          'Episodes': {
                                'title': episode_titles,
                                'plot': episode_plots,
                                'original_air_date': episode_dates,
                                'rating': episode_avg_ratings,
                                'votes': episode_votes,
                                'season_number': episode_seasons,
                                'episode_number': episode_episodes,
                                'normalized_season': normalized_season
                                }
                           })

    return jsonify(data_blob)

###################### End #########################
if __name__ == "__main__":
    app.run(debug=True)