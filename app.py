#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for,jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from sqlalchemy import func
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from extentions import csrf
from sqlalchemy.exc import SQLAlchemyError
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app,db)
csrf.init_app(app)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(100))
    created_date_time = db.Column(db.DateTime)
    shows = db.relationship('Show',backref='venue',lazy=True)

    def venues_with_datetime():
      return db.session.query(Venue).order_by(Venue.created_date_time.desc()).limit(10)

    def __repr__(self):
      return '<Venue{}>'.format(self.name)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(1000))
    website = db.Column(db.String(120))
    created_date_time = db.Column(db.DateTime)
    shows = db.relationship('Show',backref='artist',lazy=True)
    
    def artist_with_datetime():
      return db.session.query(Artist).order_by(Artist.created_date_time.desc()).limit(10)

    def __repr__(self):
      return '<Artist{}>'.format(self.name)
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#
class Show(db.Model):
    __tablename__ ='shows'
    show_id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    show_time = db.Column(db.DateTime, nullable=False)
    def __repr__(self):
      return '<Show {}{}>'.format(self.artist_id,self.venue_id)

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  artist = Artist.artist_with_datetime()
  venue = Venue.venues_with_datetime()
  return render_template('pages/home.html',artists=artist,venues=venue)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  areas_ = Venue.query.with_entities(func.count(Venue.id),Venue.city,Venue.state).group_by(Venue.city,Venue.state).all()
  data =[]
  for area in areas_:
    venues_area = Venue.query.filter_by(state = area.state).filter_by(city = area.city).all()
    venue_data = []
    for venue in venues_area:
      venue_data.append({
        "id" : venue.id,
        "name" : venue.name,
        "num_upcoming_shows" : len(db.session.query(Show).filter(Show.venue_id==1).filter(Show.show_time>datetime.now()).all())
      })
    data.append({
        "city" : area.city,
        "state" : area.state,
        "venues" : venue_data
      })
  
 

  return render_template('pages/venues.html', areas=data);

@csrf.exempt
@app.route('/venues/search', methods=['POST'])
def search_venues():
 
  search_term = request.form.get('search_term','')
  search_result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  search_data = []
  for result in search_result:
       search_data.append({
         "id" : result.id,
         "name" : result.name,
         "num_upcoming_shows" : db.session.query(Show).filter(Show.venue_id==result.id, Show.show_time>datetime.now()).count()
       })
  response ={
    "count" : len(search_result),
    "data" : search_data
    
  }     
 
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
 
  venue = Venue.query.get(venue_id)
  if not venue :
    flash('An error occured. Venue : '+ str(venue_id) + ' doesnot exists')
    return render_template('errors/404.html')
  
  upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id,Show.show_time>datetime.now())
  upcoming_shows = []
  past_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id,Show.show_time<datetime.now())
  past_shows = []

  for up_shows in upcoming_shows_query:
    upcoming_shows.append({
      "artist_id" : up_shows.artist.id,
      "artist_name" : up_shows.artist.name,
      "artist_image_link" : up_shows.artist.image_link,
      "start_time" : up_shows.show_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  for p_shows in past_shows_query:
    past_shows.append({
      "artist_id" : p_shows.artist.id,
      "artist_name" : p_shows.artist.name,
      "artist_image_link" : p_shows.artist.image_link,
      "start_time" : p_shows.show_time.strftime('%Y-%m-%d %H:%M:%S')
    }) 
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  } 
 
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
 
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form =VenueForm(request.form)
  error = False
  if form.validate():
    try:
      new_venue = Venue(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        address = request.form['address'],
        phone = request.form['phone'],
        image_link = request.form['image_link'],
        facebook_link =request.form['facebook_link'],
        genres = request.form.getlist('genres'),
        website = request.form['website'],
        seeking_talent = True if 'seeking_talent' in request.form else False,
        seeking_description = request.form['seeking_description'],
        created_date_time = datetime.now()
      )
      db.session.add(new_venue)
      db.session.commit()

    except SQLAlchemyError as e:
          error = True
          db.session.rollback()
          print(sys.exc_info())
    finally: 
          db.session.close()

    if error:
          flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')  
       
    if not error:
          flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # on successful db insert, flash success
 
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  artist = Artist.artist_with_datetime()
  venue = Venue.venues_with_datetime()
  return render_template('pages/home.html',artists=artist,venues=venue)

@app.route('/venues/<int:venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    show = Show.query.filter(Show.venue_id==venue_id).all()
    if show:
      db.session.delete(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error: 
    flash(f'An error occurred. Venue {venue_id} could not be deleted.')
  if not error: 
    flash(f'Venue {venue_id} was successfully deleted.')
  return render_template('pages/venues.html')

 

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
 
  data = db.session.query(Artist).all()
  return render_template('pages/artists.html', artists=data)

@csrf.exempt
@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  search_result = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
  data = []

  for result in search_result:
    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": db.session.query(Show).filter(Show.artist_id == result.id).filter(Show.show_time > datetime.now()).count(),
    })
  
  response={
    "count": len(search_result),
    "data": data
  }
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
 
  artist_query = db.session.query(Artist).get(artist_id)

  if not artist_query:
    flash('An error occured. Artist : '+ str(artist_id) + ' doesnot exists')
    return render_template('errors/404.html')

  gen = artist_query.genres[1:-1]
  gen_=''
  for g in gen:
    gen_ = gen_+g

  upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id,Show.show_time>datetime.now())
  upcoming_shows = []
  past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id,Show.show_time<datetime.now())
  past_shows = []

  for up_shows in upcoming_shows_query:
    upcoming_shows.append({
      "venue_id": up_shows.venue_id,
      "venue_name": up_shows.venue.name,
      "artist_image_link": up_shows.venue.image_link,
      "start_time": up_shows.show_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  for pa_shows in past_shows_query:
      past_shows.append({
      "venue_id": pa_shows.venue_id,
      "venue_name": pa_shows.venue.name,
      "artist_image_link": pa_shows.venue.image_link,
      "start_time": pa_shows.show_time.strftime('%Y-%m-%d %H:%M:%S')
      })
     
  data={
    "id": artist_query.id,
    "name": artist_query.name,
    "genres": gen_.split(","),
    "city": artist_query.city,
    "state": artist_query.state,
    "phone": artist_query.phone,
    "website": artist_query.website,
    "facebook_link": artist_query.facebook_link,
    "seeking_venue": artist_query.seeking_venue,
    "seeking_description": artist_query.seeking_description,
    "image_link": artist_query.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  
 
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  gen_=''
  

  if artist:
    for genres in artist.genres[1:-1]:
      gen_ = gen_+genres

    form.name.data = artist.name
    form.genres.data = gen_.split(',')
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.website.data = artist.website
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@csrf.exempt
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  artist = Artist.query.get(artist_id)
  error = False 

  try:
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website']
    artist.seeking_venue = True if 'seeking_venue' in request.form else False 
    artist.seeking_description = request.form['seeking_description']
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()

  if error:
    flash('Unable to update the Artist.')
  else:
    flash('Artist : '+ str(artist_id)+ ' was updated successfully')    

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  if venue: 
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.address.data = venue.address
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website.data = venue.website
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
   
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@csrf.exempt
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  
  error = False  
  venue = Venue.query.get(venue_id)

  try: 
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    venue.seeking_talent = True if 'seeking_talent' in request.form else False 
    venue.seeking_description = request.form['seeking_description']

    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    flash('Unable to update the Venue.')
  else: 
    flash('Venue :' + str(venue_id) +' was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
 
  form = ArtistForm(request.form)
  error = False
  if form.validate():
    try:
        new_artist = Artist(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        phone = request.form['phone'],
        image_link=request.form['image_link'],
        facebook_link = request.form['facebook_link'],
        genres = request.form.getlist('genres'),
        website = request.form['website'],
        seeking_venue = True if 'seeking_venue' in request.form else False,
        seeking_description = request.form['seeking_description'],
        created_date_time = datetime.now()
        )
        db.session.add(new_artist)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')    
    else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
 
  artist = Artist.artist_with_datetime()
  venue = Venue.venues_with_datetime()
  return render_template('pages/home.html',artists=artist,venues=venue)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
 
  shows_query = db.session.query(Show).join(Artist).join(Venue).all()
  data = []
  for show in shows_query:
    data.append({
      "venue_id" : show.venue_id,
      "venue_name" : show.venue.name,
      "artist_id" : show.artist_id,
      "artist_name" : show.artist.name,
      "artist_image_link" : show.artist.image_link,
      "start_time": show.show_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
 
  show = ShowForm()
  error = False
  if show.validate():
    try:
      new_show = Show(
        artist_id = request.form['artist_id'],
        venue_id = request.form['venue_id'],
        show_time = request.form['start_time']
      )
      db.session.add(new_show)
      db.session.commit()
    except:
      db.session.rollback()
      error = True
      print(sys.exc_info())
    finally:
      db.session.close()  

  if error:
      flash('An error occurred. Show could not be listed.')
  else:
      flash('Show was successfully listed!')
 
  artist = Artist.artist_with_datetime()
  venue = Venue.venues_with_datetime()
  return render_template('pages/home.html',artists=artist,venues=venue)

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
