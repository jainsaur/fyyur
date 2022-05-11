#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json

import dateutil.parser
import babel
from flask import (
  Flask, 
  render_template, 
  request, 
  flash, 
  redirect, 
  url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

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

  venue = Venue.query.get_or_404(venue_id)
  past_shows = []
  upcoming_shows = []

  for show in venue.shows:
      temp_show = {
          'artist_id': show.artist_id,
          'artist_name': show.artist.name,
          'artist_image_link': show.artist.image_link,
          'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
      }
      if show.start_time <= datetime.now():
          past_shows.append(temp_show)
      else:
          upcoming_shows.append(temp_show)

  # object class to dict
  data = vars(venue)

  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)
  
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
    form = VenueForm(request.form)

    new_city = City.query.filter(City.name == form.city.data).first()
    if new_city is None:
      new_state = State.query.filter(State.name == form.state.data).first()
      if new_state is None:
        new_state = State(name = form.state.data)
      new_city = City(name = form.city.data)
      new_city.state = new_state

    new_genres = []
    for genre in form.genres.data:
      new_genre = Genre.query.filter(Genre.name == genre).first()
      if new_genre is None:
        new_genre = Genre(name = genre)
      new_genres.append(new_genre)

    new_venue = Venue(
      name = form.name.data,
      address = form.address.data,
      phone = form.phone.data,
      image_link = form.image_link.data,
      facebook_link = form.facebook_link.data,
      website_link = form.website_link.data,
      seeking_talent = form.seeking_talent.data,
      seeking_description = form.seeking_description.data
    )

    new_venue.city = new_city
    new_venue.genres = new_genres

    db.session.add(new_venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + form.name.data + ' was successfully listed!')
  except Exception as e:
    print(e)
    db.session.rollback()
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.', 'error')

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

  artist = Artist.query.get_or_404(artist_id)
  past_shows = []
  upcoming_shows = []

  for show in artist.shows:
      temp_show = {
          'venue_id': show.venue_id,
          'venue_name': show.venue.name,
          'venue_image_link': show.venue.image_link,
          'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
      }
      if show.start_time <= datetime.now():
          past_shows.append(temp_show)
      else:
          upcoming_shows.append(temp_show)

  # object class to dict
  data = vars(artist)

  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)

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
    form = ArtistForm(request.form)
    
    new_city = City.query.filter(City.name == form.city.data).first()
    if new_city is None:
      new_state = State.query.filter(State.name == form.state.data).first()
      if new_state is None:
        new_state = State(name = form.state.data)
      new_city = City(name = form.city.data)
      new_city.state = new_state

    new_genres = []
    for genre in form.genres.data:
      new_genre = Genre.query.filter(Genre.name == genre).first()
      if new_genre is None:
        new_genre = Genre(name = genre)
      new_genres.append(new_genre)

    new_artist = Artist(
      name = form.name.data,
      phone = form.phone.data,
      image_link = form.image_link.data,
      facebook_link = form.facebook_link.data,
      website_link = form.website_link.data,
      seeking_venue = form.seeking_venue.data,
      seeking_description = form.seeking_description.data
    )

    new_artist.city = new_city
    new_artist.genres = new_genres

    db.session.add(new_artist)
    db.session.commit()
    flash('Artist ' + form.name.data + ' was successfully listed!')
  except Exception as e:
    print(e)
    db.session.rollback()
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.', 'error')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  all_shows = Show.query.all()
  data = []
  for show in all_shows:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time)
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  try:
    form = ShowForm(request.form)

    venue_id = int(form.venue_id.data)
    venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
    artist_id = int(form.artist_id.data)
    artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
    
    new_show = Show(start_time = form.start_time.data)
    new_show.venue = venue
    new_show.artist = artist

    db.session.add(new_show)
    db.session.commit()
    flash('Show was successfully listed!')
  except Exception as e:
    print(e)
    db.session.rollback()
    flash('Error occurred while listing the show', 'error')
  
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
