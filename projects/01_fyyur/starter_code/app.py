#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json

from sqlalchemy import ForeignKey, Table, Column, null
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class State(db.Model):
  __tablename__ = 'states'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(120), nullable=False, index=True)

  cities = db.relationship('City', backref=db.backref("state", lazy=True))

class City(db.Model):
  __tablename__ = 'cities'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(120), nullable=False, index=True)
  state_id = db.Column(db.Integer, ForeignKey('states.id'), nullable=False)

  venues = db.relationship('Venue', backref=db.backref("city", lazy=True))
  artists = db.relationship('Artist', backref=db.backref("city", lazy=True))

class Genre(db.Model):
  __tablename__ = 'genres'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(120), nullable=False, index=True)

venue_genres_table = Table(
  'venue_genres_association', 
  db.Model.metadata,
  Column('venue_id', ForeignKey('venues.id'), primary_key=True),
  Column('genre_id', ForeignKey('genres.id'), primary_key=True)
)

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city_id = db.Column(db.Integer, ForeignKey('cities.id'), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(1024))

    genres = db.relationship("Genre", secondary=venue_genres_table, backref=db.backref("venues", lazy=True))

artist_genres_table = Table(
  'artist_genres_association', 
  db.Model.metadata,
  Column('artist_id', ForeignKey('artists.id'), primary_key=True),
  Column('genre_id', ForeignKey('genres.id'), primary_key=True)
)

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city_id = db.Column(db.Integer, ForeignKey('cities.id'), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(1024))

    genres = db.relationship("Genre", secondary=artist_genres_table, backref=db.backref("artists", lazy=True))
    shows = db.relationship("Show", backref=db.backref("artist", lazy=True))

class Show(db.Model):
  __tablename__ = 'shows'

  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), primary_key=True)
  start_time = db.Column(db.DateTime, nullable=False)

  venue = db.relationship("Venue", backref=db.backref("shows", lazy=True))

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = City.query.all()
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form['search_term']
  data = db.session.query(Venue.id, Venue.name).filter(Venue.name.ilike(f"%{search_term}%")).all()
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  data = db.session.query(Venue).filter(Venue.id==venue_id).first()
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    new_city = City.query.filter(City.name == request.form['city']).first()
    if new_city is None:
      new_state = State.query.filter(State.name == request.form['state']).first()
      if new_state is None:
        new_state = State(name = request.form['state'])
      new_city = City(name = request.form['city'])
      new_city.state = new_state

    new_genres = []
    for genre in request.form.getlist('genres'):
      new_genre = Genre.query.filter(Genre.name == genre).first()
      if new_genre is None:
        new_genre = Genre(name = genre)
      new_genres.append(new_genre)

    new_seeking_talent = False
    if 'seeking_talent' in request.form:
      new_seeking_talent = True

    new_venue = Venue(
      name = request.form['name'],
      address = request.form['address'],
      phone = request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      website_link = request.form['website_link'],
      seeking_talent = new_seeking_talent,
      seeking_description = request.form['seeking_description']
    )

    new_venue.city = new_city
    new_venue.genres = new_genres

    db.session.add(new_venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    print(e)
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.', 'error')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    query = db.session.query(Venue).filter(Venue.id==venue_id)
    query.delete()
    flash("Venue successfully deleted")
  except:
    flash("Error occurred while deleting venue", 'error')

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form['search_term']
  data = db.session.query(Artist.id, Artist.name).filter(Artist.name.ilike(f"%{search_term}%")).all()
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data = db.session.query(Artist).filter(Artist.id==artist_id).first()
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist=db.session.query(Artist).filter(Artist.id==artist_id).first()
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    artist=db.session.query(Artist).filter(Artist.id==artist_id).first()

    if request.form['city'] != '' and artist.city.name != request.form['city']:
      new_city = City.query.filter(City.name == request.form['city']).first()
      if new_city is None:
        new_state = State.query.filter(State.name == request.form['state']).first()
        if new_state is None:
          new_state = State(name = request.form['state'])
        new_city = City(name = request.form['city'])
        new_city.state = new_state
      artist.city = new_city

    if len(request.form.getlist('genres')) > 0:
      new_genres = []
      for genre in request.form.getlist('genres'):
        new_genre = Genre.query.filter(Genre.name == genre).first()
        if new_genre is None:
          new_genre = Genre(name = genre)
        new_genres.append(new_genre)
      artist.genres = new_genres

    new_seeking_venue = False
    if 'seeking_venue' in request.form:
      new_seeking_venue = True

    artist.name = request.form['name']
    artist.phone = request.form['phone']
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website_link = request.form['website_link']
    artist.seeking_venue = new_seeking_venue
    artist.seeking_description = request.form['seeking_description']

    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except Exception as e:
    print(e)
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.', 'error')
  

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue=db.session.query(Venue).filter(Venue.id==venue_id).first()
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    venue=db.session.query(Venue).filter(Venue.id==venue_id).first()

    if request.form['city'] != '' and venue.city.name != request.form['city']:
      new_city = City.query.filter(City.name == request.form['city']).first()
      if new_city is None:
        new_state = State.query.filter(State.name == request.form['state']).first()
        if new_state is None:
          new_state = State(name = request.form['state'])
        new_city = City(name = request.form['city'])
        new_city.state = new_state
      venue.city = new_city

    if len(request.form.getlist('genres')) > 0:
      new_genres = []
      for genre in request.form.getlist('genres'):
        new_genre = Genre.query.filter(Genre.name == genre).first()
        if new_genre is None:
          new_genre = Genre(name = genre)
        new_genres.append(new_genre)
      venue.genres = new_genres

    new_seeking_talent = False
    if 'seeking_talent' in request.form:
      new_seeking_talent = True

    venue.name = request.form['name'],
    venue.address = request.form['address'],
    venue.phone = request.form['phone'],
    venue.image_link = request.form['image_link'],
    venue.facebook_link = request.form['facebook_link'],
    venue.website_link = request.form['website_link'],
    venue.seeking_talent = new_seeking_talent,
    venue.seeking_description = request.form['seeking_description']
    
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except Exception as e:
    print(e)
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.', 'error')

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    new_city = City.query.filter(City.name == request.form['city']).first()
    if new_city is None:
      new_state = State.query.filter(State.name == request.form['state']).first()
      if new_state is None:
        new_state = State(name = request.form['state'])
      new_city = City(name = request.form['city'])
      new_city.state = new_state

    new_genres = []
    for genre in request.form.getlist('genres'):
      new_genre = Genre.query.filter(Genre.name == genre).first()
      if new_genre is None:
        new_genre = Genre(name = genre)
      new_genres.append(new_genre)

    new_seeking_venue = False
    if 'seeking_venue' in request.form:
      new_seeking_venue = True

    new_artist = Artist(
      name = request.form['name'],
      phone = request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      website_link = request.form['website_link'],
      seeking_venue = new_seeking_venue,
      seeking_description = request.form['seeking_description']
    )

    new_artist.city = new_city
    new_artist.genres = new_genres

    db.session.add(new_artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    print(e)
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.', 'error')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data=[{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21T21:30:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15T23:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-01T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-08T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-15T20:00:00.000Z"
  }]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
