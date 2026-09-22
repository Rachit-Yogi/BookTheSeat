const state={user:null,firebaseUser:null,config:null,currentMovie:null,currentTheatre:null,currentShow:null,currentShowData:null,lastSeatSnap:null,selectedSeats:new Set(),reservations:[],expiresAt:null,ws:null,location:null,authConfirmation:null};
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));
const fmtINR=n=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(Number(n||0));
const todayISO=()=>new Date().toISOString().slice(0,10);
const navigate=(view,params={})=>{const q=new URLSearchParams(params).toString();location.hash=view+(q?'?'+q:'')};
const hashView=()=>{const [v,q='']=location.hash.slice(1).split('?');return[v||'home',new URLSearchParams(q)]};
const toast=(msg,type='info')=>{const root=$('#toast-root');if(!root)return;const el=document.createElement('div');el.className='toast '+type;el.textContent=msg;root.appendChild(el);setTimeout(()=>el.remove(),3200)};
async function api(path,opts={}){
  const headers={...(opts.headers||{}),'Content-Type':'application/json'};
  if(state.firebaseUser?.getIdToken) headers.Authorization='Bearer '+await state.firebaseUser.getIdToken();
  const res=await fetch(path,{...opts,headers});
  const data=await res.json().catch(()=>({}));
  if(!res.ok)throw new Error(data.detail||'Something went wrong');
  return data;
}
async function boot(){
  state.config=await api('/api/config');
  await initFirebase();
  if(localStorage.getItem('bts_demo')) await demoLogin(false);
  $('#location-pill')?.addEventListener('click',useLocation);
  window.addEventListener('hashchange',renderRoute);
  await renderRoute();
  updateAuthButton();
}
async function initFirebase(){
  const f=state.config?.firebase||{};
  if(!f.projectId||typeof firebase==='undefined')return;
  try{
    if(!firebase.apps.length)firebase.initializeApp(f);
    firebase.auth().onAuthStateChanged(async u=>{
      state.firebaseUser=u;
      if(u){
        try{state.user=await api('/api/auth/login',{method:'POST',body:JSON.stringify({id_token:await u.getIdToken()})})}catch(e){toast(e.message,'error')}
      }else if(!localStorage.getItem('bts_demo'))state.user=null;
      updateAuthButton();
    });
  }catch(e){console.warn(e)}
}
function updateAuthButton(){
  const b=$('#auth-button');if(!b)return;
  b.textContent=state.user?'Account':'Login';
  b.onclick=state.user?()=>navigate('profile'):openAuth;
}
function openAuth(){$('#auth-modal')?.showModal();$('#auth-error').textContent=''}
function closeAuth(){$('#auth-modal')?.close()}
async function googleLogin(){
  if(typeof firebase==='undefined'){toast('Firebase is not configured. Use demo account.','error');return}
  try{await firebase.auth().signInWithPopup(new firebase.auth.GoogleAuthProvider());closeAuth();toast('Signed in successfully','success')}catch(e){$('#auth-error').textContent=e.message}
}
async function sendOtp(){
  try{
    const phone=$('#phone-number').value.trim();if(!phone)throw new Error('Enter a phone number');
    if(!window.recaptchaVerifier)window.recaptchaVerifier=new firebase.auth.RecaptchaVerifier('recaptcha-container',{size:'invisible'});
    state.authConfirmation=await firebase.auth().signInWithPhoneNumber(phone,window.recaptchaVerifier);
    $('#otp-row').classList.remove('hidden');toast('OTP sent','success')
  }catch(e){$('#auth-error').textContent=e.message}
}
async function verifyOtp(){
  try{await state.authConfirmation.confirm($('#phone-otp').value.trim());closeAuth();toast('Phone verified','success')}catch(e){$('#auth-error').textContent=e.message}
}
async function demoLogin(showToast=true){
  const token='demo:demo-user:demo@booktheseat.local';
  try{
    state.firebaseUser={getIdToken:async()=>token};
    state.user=await api('/api/auth/login',{method:'POST',body:JSON.stringify({id_token:token})});
    localStorage.setItem('bts_demo','1');updateAuthButton();if(showToast){closeAuth();toast('Demo account ready','success')}
    return true
  }catch(e){toast(e.message,'error');return false}
}
function requireAuth(){if(state.user)return true;openAuth();return false}
function useLocation(){
  if(!navigator.geolocation){toast('Location is unavailable in this browser','error');return}
  navigator.geolocation.getCurrentPosition(p=>{state.location={lat:p.coords.latitude,lon:p.coords.longitude};$('#location-pill').textContent='📍 Nearby';toast('Using your location','success');renderRoute()},()=>toast('Location permission was not granted','error'))
}
function movieCard(m){return'<article class="movie-card" onclick="navigate(\'movie\',{id:'+m.movie_id+'})"><div class="poster"><img loading="lazy" src="'+esc(m.poster_url)+'" alt="'+esc(m.title)+'"></div><div class="movie-meta"><h3>'+esc(m.title)+'</h3><div class="meta-line"><span>'+esc(m.language)+'</span><span class="rating">★ '+Number(m.rating).toFixed(1)+'</span></div><div class="meta-line"><span>'+esc((m.genre||'').split(',')[0])+'</span><span>'+m.duration+'m</span></div></div></article>'}
async function renderRoute(){
  if(state.ws){state.ws.close();state.ws=null}
  const [view,q]=hashView();
  try{
    if(view==='home')return renderHome();
    if(view==='movies')return renderMovies(q);
    if(view==='movie')return renderMovie(Number(q.get('id')));
    if(view==='theatres')return renderTheatres();
    if(view==='shows')return renderShows(Number(q.get('movie')),Number(q.get('theatre')),q.get('date')||todayISO());
    if(view==='seats')return renderSeats(Number(q.get('show')));
    if(view==='checkout')return renderCheckout();
    if(view==='confirmation')return renderConfirmation();
    if(view==='profile')return renderProfile();
    return renderHome();
  }catch(e){$('#app').innerHTML='<section class="page"><div class="empty"><h2>Oops.</h2><p>'+esc(e.message)+'</p><button class="primary-btn" onclick="navigate(\'home\')">Back home</button></div></section>'}
}
async function renderHome(){
  const movies=await api('/api/movies?sort=rating&limit=20');
  const now=movies.filter(m=>new Date(m.release_date)<=new Date()).slice(0,10);
  $('#app').innerHTML='<section class="page hero"><div><div class="eyebrow">MOVIE NIGHTS, SORTED.</div><h1>Pick a seat.<br><span>Make a memory.</span></h1><p>Discover Jaipur theatres, lock seats live, and finish a simulated checkout in one smooth flow.</p><div style="display:flex;gap:10px;margin-top:22px"><button class="primary-btn" onclick="navigate(\'movies\')">Explore movies</button><button class="secondary-btn" onclick="navigate(\'theatres\')">Find theatres</button></div></div><div class="hero-visual"><div class="hero-ticket"><strong>Live booking demo</strong><small>5-minute seat hold · WebSocket updates · QR confirmation</small></div></div></section><section class="page"><div class="section-head"><div><h2>Trending in Jaipur</h2><p>Sample catalogue seeded for the demo.</p></div><button class="ghost-btn" onclick="navigate(\'movies\')">See all</button></div><div class="movie-grid">'+movies.slice(0,8).map(movieCard).join('')+'</div><div class="section-head"><div><h2>Now showing</h2><p>Movies available in the seeded theatre schedule.</p></div></div><div class="movie-grid">'+now.map(movieCard).join('')+'</div></section>'
}
async function renderMovies(q){
  const qs=new URLSearchParams({limit:'50'});
  if(q.get('search'))qs.set('q',q.get('search'));if(q.get('genre'))qs.set('genre',q.get('genre'));if(q.get('sort'))qs.set('sort',q.get('sort'));
  const movies=await api('/api/movies?'+qs);
  $('#app').innerHTML='<section class="page"><div class="section-head"><div><div class="eyebrow">DISCOVER</div><h2>Movies</h2><p>Search by title, genre or language.</p></div></div><div class="filter-bar"><div class="search-bar">🔎<input id="movie-search" value="'+esc(q.get('search')||'')+'" placeholder="Search movies..." onkeydown="if(event.key===\'Enter\')movieFilter()"><button class="ghost-btn" onclick="movieFilter()">Search</button></div><div class="field"><label>Genre</label><select id="movie-genre" onchange="movieFilter()"><option value="">All genres</option><option>Action</option><option>Comedy</option><option>Drama</option><option>Horror</option><option>Sci-Fi</option><option>Thriller</option></select></div><div class="field"><label>Sort</label><select id="movie-sort" onchange="movieFilter()"><option value="popularity">Popularity</option><option value="rating">Rating</option><option value="release">Release date</option></select></div></div><div class="pill-row" style="margin:16px 0">'+['Action','Comedy','Drama','Horror','Sci-Fi','Thriller'].map(g=>'<button class="pill '+(q.get('genre')===g?'active':'')+'" onclick="navigate(\'movies\',{genre:\''+g+'\'})">'+g+'</button>').join('')+'</div><div class="movie-grid">'+(movies.length?movies.map(movieCard).join(''):'<div class="empty" style="grid-column:1/-1">No movies found.</div>')+'</div></section>';
  $('#movie-genre').value=q.get('genre')||'';$('#movie-sort').value=q.get('sort')||'popularity'
}
function movieFilter(){navigate('movies',{search:$('#movie-search').value,genre:$('#movie-genre').value,sort:$('#movie-sort').value})}
async function renderMovie(id){
  const m=await api('/api/movies/'+id);state.currentMovie=m;
  $('#app').innerHTML='<section class="page"><div class="movie-detail"><div class="detail-poster"><img src="'+esc(m.poster_url)+'" alt="'+esc(m.title)+'"></div><div class="detail-copy"><div class="eyebrow">MOVIE DETAILS</div><h1>'+esc(m.title)+'</h1><div class="detail-stats"><span class="stat">★ <strong>'+Number(m.rating).toFixed(1)+'</strong></span><span class="stat"><strong>'+esc(m.language)+'</strong></span><span class="stat">'+m.duration+' min</span><span class="stat">'+m.release_date+'</span></div><p class="tagline">'+esc(m.description)+'</p><p class="muted"><strong>Genre:</strong> '+esc(m.genre)+'<br><strong>Cast:</strong> '+esc(m.cast)+'</p><button class="primary-btn" onclick="startBooking('+m.movie_id+')">Book tickets</button></div></div></section>'
}
async function startBooking(movieId){const theatres=await api('/api/theatres?city=Jaipur'+(state.location?'&latitude='+state.location.lat+'&longitude='+state.location.lon:''));if(!theatres.length){toast('No theatres available','error');return}navigate('shows',{movie:movieId,theatre:theatres[0].theatre_id,date:todayISO()})}
async function renderTheatres(){
  const theatres=await api('/api/theatres?city=Jaipur'+(state.location?'&latitude='+state.location.lat+'&longitude='+state.location.lon:''));
  $('#app').innerHTML='<section class="page"><div class="section-head"><div><div class="eyebrow">JAIPUR</div><h2>Theatres</h2><p>'+ (state.location?'Sorted by distance from your location.':'Use the location button to sort by distance.')+'</p></div></div><div class="theatre-list">'+theatres.map(t=>'<article class="theatre-card"><div><h3>'+esc(t.name)+'</h3><p>'+esc(t.location)+'</p></div><div class="distance">'+(t.distance_km!=null?t.distance_km+' km':'Jaipur')+'</div></article>').join('')+'</div></section>'
}
async function renderShows(movieId,theatreId,showDate){
  const [m,t,shows]=await Promise.all([api('/api/movies/'+movieId),api('/api/theatres?city=Jaipur'),api('/api/showtimes/'+movieId+'/'+theatreId+'/'+showDate)]);
  state.currentMovie=m;state.currentTheatre=t.find(x=>x.theatre_id===theatreId)||null;
  const dates=Array.from({length:6},(_,i)=>{const d=new Date();d.setDate(d.getDate()+i);return d.toISOString().slice(0,10)});
  $('#app').innerHTML='<section class="page"><div class="section-head"><div><div class="eyebrow">SHOWTIMES</div><h2>'+esc(m.title)+'</h2><p>'+esc(state.currentTheatre?.name||'Theatre')+'</p></div><button class="ghost-btn" onclick="navigate(\'movie\',{id:'+m.movie_id+'})">← Movie</button></div><div class="date-strip">'+dates.map(d=>'<button class="date-chip '+(d===showDate?'active':'')+'" onclick="navigate(\'shows\',{movie:'+movieId+',theatre:'+theatreId+',date:\''+d+'\'})">'+d.slice(5)+'</button>').join('')+'</div><div class="section-head"><div><h2>Available shows</h2><p>'+shows.length+' show(s) · seats shown after selection</p></div></div><div class="show-grid">'+(shows.length?shows.map(s=>'<article class="show-card" onclick="navigate(\'seats\',{show:'+s.showtime_id+'})"><div class="time">'+s.time+'</div><div class="show-sub">'+s.format+' · '+esc(s.language)+'</div><div class="show-sub">'+s.available_seats+' seats left · '+fmtINR(s.min_price)+'–'+fmtINR(s.max_price)+'</div></article>').join(''):'<div class="empty" style="grid-column:1/-1">No shows for this date.</div>')+'</div></section>'
}
async function renderSeats(showId){
  if(!requireAuth())return;state.currentShow=showId;state.selectedSeats=new Set();
  const [snap,info]=await Promise.all([api('/api/seats/'+showId),api('/api/showtimes/by-id/'+showId)]);
  state.lastSeatSnap=snap;state.currentShowData=info;state.currentMovie=info.movie;state.currentTheatre=info.theatre;
  $('#app').innerHTML='<section class="page"><div class="section-head"><div><div class="eyebrow">SELECT YOUR SEATS</div><h2>'+esc(info.movie.title)+'</h2><p>'+esc(info.theatre.name)+' · '+info.date+' · '+info.time+'</p></div></div><div class="seat-shell"><div class="seat-panel"><div class="screen"></div><div class="screen-label">SCREEN THIS WAY</div><div id="seat-map"></div><div class="legend"><span><i></i>Standard</span><span class="p"><i></i>Premium</span><span class="r"><i></i>Recliner</span><span class="s"><i></i>Selected</span><span class="b"><i></i>Booked / held</span></div></div><aside class="summary-card"><h3>Your selection</h3><div id="selected-list" class="muted">No seats selected</div><div class="summary-line total"><span>Total</span><strong id="seat-total">₹0</strong></div><button id="continue-seat" class="primary-btn wide" onclick="reserveSelected()" disabled>Continue</button><p class="warning" style="margin-top:12px">Seats are locked for '+(state.config?.reservationMinutes||5)+' minutes after you continue.</p></aside></div></section>';
  drawSeatMap(snap.seats);connectSeatSocket(showId)
}
function drawSeatMap(seats){
  const map=$('#seat-map');if(!map)return;const byRow={};seats.forEach(s=>(byRow[s.row_letter]??=[]).push(s));
  map.innerHTML=Object.entries(byRow).map(([row,arr])=>'<div class="seat-row"><span class="row-label">'+row+'</span>'+arr.map(s=>'<button class="seat '+s.seat_type+' '+(s.is_booked?'booked ':'')+(s.is_reserved?'reserved ':'')+(state.selectedSeats.has(s.seat_id)?'selected':'')+'" title="'+s.seat_number+' · '+fmtINR(s.price)+'" '+(s.is_booked||s.is_reserved?'disabled':'')+' onclick="toggleSeat('+s.seat_id+')">'+s.seat_number.replace(row,'')+'</button>').join('')+'</div>').join('')
}
function toggleSeat(id){
  if(state.selectedSeats.has(id))state.selectedSeats.delete(id);
  else{if(state.selectedSeats.size>=10){toast('Maximum 10 seats per reservation','error');return}state.selectedSeats.add(id)}
  drawSeatMap(state.lastSeatSnap.seats);updateSeatSummary()
}
function updateSeatSummary(){
  const selected=state.lastSeatSnap.seats.filter(s=>state.selectedSeats.has(s.seat_id));
  $('#selected-list').innerHTML=selected.length?selected.map(s=>'<div class="summary-line"><span>'+s.seat_number+'</span><strong>'+fmtINR(s.price)+'</strong></div>').join(''):'No seats selected';
  $('#seat-total').textContent=fmtINR(selected.reduce((a,s)=>a+Number(s.price),0));$('#continue-seat').disabled=!selected.length
}
function connectSeatSocket(showId){
  try{
    state.ws=new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws/seats/'+showId);
    state.ws.onmessage=e=>{const p=JSON.parse(e.data);if(p.seats){state.lastSeatSnap=p;drawSeatMap(p.seats);updateSeatSummary()}};
  }catch(e){}
}
async function reserveSelected(){
  try{
    const res=await api('/api/reserve-seats',{method:'POST',body:JSON.stringify({showtime_id:state.currentShow,seat_ids:[...state.selectedSeats]})});
    state.reservations=res.reservation_ids;state.expiresAt=new Date(res.expires_at);sessionStorage.setItem('bts_checkout',JSON.stringify(res));navigate('checkout')
  }catch(e){toast(e.message,'error')}
}
let timerInterval=null;
async function renderCheckout(){
  if(!requireAuth())return;const data=JSON.parse(sessionStorage.getItem('bts_checkout')||'null');if(!data){navigate('home');return}
  state.reservations=data.reservation_ids;state.expiresAt=new Date(data.expires_at);state.currentShow=data.showtime_id;state.currentMovie=data.movie;state.currentTheatre=data.theatre;
  $('#app').innerHTML='<section class="page"><div class="section-head"><div><div class="eyebrow">CHECKOUT</div><h2>Confirm your booking</h2><p>Your seats are held temporarily. Complete simulated payment before the timer ends.</p></div></div><div class="checkout-grid"><div class="summary-card" style="position:static"><h3>Order summary</h3><div class="summary-line"><span>Movie</span><strong>'+esc(data.movie?.title||'Movie')+'</strong></div><div class="summary-line"><span>Theatre</span><strong>'+esc(data.theatre?.name||'Theatre')+'</strong></div><div class="summary-line"><span>Show</span><strong>'+data.date+' · '+data.time+'</strong></div><div class="summary-line"><span>Seats</span><strong>'+data.seats.map(s=>s.seat_number).join(', ')+'</strong></div><div class="summary-line total"><span>Total</span><strong>'+fmtINR(data.total)+'</strong></div></div><aside class="summary-card"><div class="eyebrow">PAYMENT WINDOW</div><div id="countdown" class="timer">05:00</div><p class="warning">Reserved seats release automatically when the timer expires.</p><button class="primary-btn wide" onclick="payNow()">Book Now — '+fmtINR(data.total)+'</button><button class="ghost-btn wide" style="margin-top:10px" onclick="cancelCheckout()">Cancel</button></aside></div></section>';
  startTimer()
}
function startTimer(){
  clearInterval(timerInterval);const tick=()=>{const sec=Math.max(0,Math.ceil((state.expiresAt-Date.now())/1000));const el=$('#countdown');if(!el)return;el.textContent=String(Math.floor(sec/60)).padStart(2,'0')+':'+String(sec%60).padStart(2,'0');if(sec<=60)el.style.color='#ffc65a';if(sec<=0){clearInterval(timerInterval);cancelCheckout(true)}};tick();timerInterval=setInterval(tick,500)
}
async function cancelCheckout(expired=false){
  clearInterval(timerInterval);
  try{if(state.reservations?.length)await api('/api/cancel-reservation',{method:'POST',body:JSON.stringify({reservation_ids:state.reservations})});sessionStorage.removeItem('bts_checkout');toast(expired?'Payment window expired — seats released':'Seats released',expired?'error':'info');navigate('seats',{show:state.currentShow})}catch(e){toast(e.message,'error')}
}
async function payNow(){
  try{const res=await api('/api/book-tickets',{method:'POST',body:JSON.stringify({reservation_ids:state.reservations})});clearInterval(timerInterval);sessionStorage.setItem('bts_confirmation',JSON.stringify(res));sessionStorage.removeItem('bts_checkout');navigate('confirmation');toast('Payment simulated successfully','success')}catch(e){toast(e.message,'error')}
}
async function renderConfirmation(){
  const b=JSON.parse(sessionStorage.getItem('bts_confirmation')||'null');if(!b){navigate('home');return}
  $('#app').innerHTML='<section class="page"><div class="confirmation"><div class="eyebrow">PAYMENT SUCCESSFUL</div><h1>Booking confirmed 🎟️</h1><p class="muted">Keep the QR handy at the theatre.</p><img class="qr" src="'+b.qr_data+'" alt="Booking QR"><div class="booking-code">'+esc(b.booking_ref)+'</div><div style="text-align:left;margin-top:26px"><div class="summary-line"><span>Movie</span><strong>'+esc(b.movie)+'</strong></div><div class="summary-line"><span>Theatre</span><strong>'+esc(b.theatre)+'</strong></div><div class="summary-line"><span>Show</span><strong>'+b.date+' · '+b.time+'</strong></div><div class="summary-line"><span>Seats</span><strong>'+b.seats.join(', ')+'</strong></div><div class="summary-line total"><span>Paid</span><strong>'+fmtINR(b.total_price)+'</strong></div></div><div style="display:flex;gap:10px;margin-top:22px"><button class="primary-btn" onclick="downloadQR()">Download QR</button><button class="secondary-btn" onclick="navigate(\'profile\')">My bookings</button></div></div></section>'
}
function downloadQR(){const b=JSON.parse(sessionStorage.getItem('bts_confirmation')||'null');if(!b)return;const a=document.createElement('a');a.href=b.qr_data;a.download=b.booking_ref+'.png';a.click()}
async function renderProfile(){
  if(!requireAuth())return;const [me,bookings]=await Promise.all([api('/api/me'),api('/api/me/bookings')]);
  $('#app').innerHTML='<section class="page"><div class="section-head"><div><div class="eyebrow">ACCOUNT</div><h2>'+esc(me.email||me.phone_number||'BookTheSeat user')+'</h2><p>Manage your profile and booking history.</p></div><button class="ghost-btn" onclick="logout()">Sign out</button></div><div class="summary-card" style="position:static;margin-bottom:20px"><div class="summary-line"><span>Email</span><strong>'+esc(me.email||'—')+'</strong></div><div class="summary-line"><span>Phone</span><strong>'+esc(me.phone_number||'—')+'</strong></div></div><div class="section-head"><div><h2>Booking history</h2><p>'+bookings.length+' booking(s)</p></div></div><div class="history-grid">'+(bookings.length?bookings.map(b=>'<div class="history-card"><img src="'+esc(b.movie_poster)+'" alt=""><div style="flex:1"><h3 style="margin:0 0 6px">'+esc(b.movie)+'</h3><p class="muted" style="margin:0">'+esc(b.theatre)+' · '+b.date+' · '+b.time+'<br>Seats: '+b.seats.join(', ')+' · '+fmtINR(b.total_price)+'</p></div><span class="pill '+(b.status==='confirmed'?'active':'')+'">'+b.status+'</span></div>').join(''):'<div class="empty">No bookings yet.</div>')+'</div></section>'
}
async function logout(){
  try{if(typeof firebase!=='undefined'&&firebase.apps.length)await firebase.auth().signOut()}catch(e){}
  state.firebaseUser=null;state.user=null;localStorage.removeItem('bts_demo');updateAuthButton();navigate('home');toast('Signed out','info')
}
boot();
