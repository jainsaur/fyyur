from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Table, Column

db = SQLAlchemy()

class State(db.Model):
  __tablename__ = 'states'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(120), nullable=False, index=True)

  cities = db.relationship(
      'City', 
      backref=db.backref("state", lazy="joined", cascade="all, delete"), 
      lazy="joined", 
      cascade="all, delete"
    )

class City(db.Model):
  __tablename__ = 'cities'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(120), nullable=False, index=True)
  state_id = db.Column(db.Integer, ForeignKey('states.id'), nullable=False)

  venues = db.relationship(
      'Venue', 
      backref=db.backref("city", lazy="joined", cascade="all, delete"), 
      lazy="joined", 
      cascade="all, delete"
    )
  artists = db.relationship(
      'Artist', 
      backref=db.backref("city", lazy="joined", cascade="all, delete"), 
      lazy="joined", 
      cascade="all, delete"
    )

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

    genres = db.relationship(
        "Genre", 
        secondary=venue_genres_table, 
        backref=db.backref("venues", lazy="joined", cascade="all, delete"), 
        lazy="joined", 
        cascade="all, delete"
    )

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

    genres = db.relationship(
        "Genre", 
        secondary=artist_genres_table, 
        backref=db.backref("artists", lazy="joined", cascade="all, delete"),
        lazy="joined", 
        cascade="all, delete"
    )
    shows = db.relationship(
        "Show", 
        backref=db.backref("artist", lazy="joined", cascade="all, delete"), 
        lazy="joined", 
        cascade="all, delete"
    )

class Show(db.Model):
  __tablename__ = 'shows'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)

  venue = db.relationship(
      "Venue", 
      backref=db.backref("shows", lazy="joined", cascade="all, delete"),
      lazy="joined", 
      cascade="all, delete")