var is_on_touch_device = !!("ontouchstart" in window) || window.navigator.msMaxTouchPoints > 0;

//////// CAPO ////////
var capo_minus_button = document.getElementById("IDcapoMinusButton");
var capo_plus_button = document.getElementById("IDcapoPlusButton");
var current_capo_value;
var current_capo_value_int;

// Capo minus -> transpose chords +1
capo_minus_button.addEventListener("click", () => {
    if (spotify_error == 1) {
        // Make button unclickable if Spotify is not available
        return;
    }
    current_capo_value = document.getElementById("IDguitarCapo");
    current_capo_value_int = parseInt(current_capo_value.innerHTML);
    if (current_capo_value_int > 0) {
        current_capo_value_int -= 1;
        current_capo_value.innerHTML = current_capo_value_int;
        capo_minus_button.style.opacity = "1";
        capo_plus_button.style.opacity = "1";
        
        // Apply chord transpose (minus 1 capo) for main_chords_body
        var parser = new DOMParser();
        var parsed_body = parser.parseFromString(document.getElementById('IDdivMainChords').innerHTML, "text/html");
        var all_chords = parsed_body.getElementsByClassName("chord_span");
        for (let i = 0; i < all_chords.length; i++) {
            all_chords[i].innerHTML = sharOrFlatTranposer(transposeChord(all_chords[i].innerHTML.toString(), 1), current_flat_or_sharp);
        }
        document.getElementById('IDdivMainChords').innerHTML = parsed_body.body.innerHTML;
        main_chords_body = parsed_body.body.innerHTML;
    }

    if (current_capo_value_int == 0) {
        capo_minus_button.style.opacity = "0.5";
        capo_plus_button.style.opacity = "1";
    } 
    if (initial_capo_value == current_capo_value_int) {
        current_capo_value.style.fontWeight = "bold";
        current_capo_value.style.color = "#1DB954";
    } else {
        current_capo_value.style.fontWeight = "normal";
        current_capo_value.style.color = "#1DB954";
    }

    // Check current_flat_or_sharp after capo change
    var parser3 = new DOMParser();
    var parsed_body_3 = parser3.parseFromString(document.getElementById('IDdivMainChords').innerHTML, "text/html");
    var all_chords_3 = parsed_body_3.getElementsByClassName("chord_span");
    amount_of_flats = 0;
    amount_of_sharps = 0;
    for (let i = 0; i < all_chords_3.length; i++) {
        amount_of_flats += (all_chords_3[i].innerHTML.match(/b/g) || []).length;
    }
    for (let i = 0; i < all_chords_3.length; i++) {
        amount_of_sharps += (all_chords_3[i].innerHTML.match(/#/g) || []).length;
    }
    if (amount_of_sharps > amount_of_flats) {
        document.getElementById("IDsharpSymbol").style.fontWeight = "bold";
        document.getElementById("IDsharpSymbol").style.color = "#1DB954";
        current_flat_or_sharp = "#";
    }
    if (amount_of_flats > amount_of_sharps) {
        document.getElementById("IDflatSymbol").style.fontWeight = "bold";
        document.getElementById("IDflatSymbol").style.color = "#1DB954";
        current_flat_or_sharp = "b";
    }
    if (amount_of_sharps == amount_of_flats) {
        document.getElementById("IDsharpSymbol").style.fontWeight = "normal";
        document.getElementById("IDsharpSymbol").style.color = "white";
        document.getElementById("IDflatSymbol").style.fontWeight = "normal";
        document.getElementById("IDflatSymbol").style.color = "white";
        // Do not reasign current_flat_or_sharp to persist the previous value when changing capo afterwards again
    }
});

// Capo plus -> transpose chords -1
capo_plus_button.addEventListener("click", () => {
    if (spotify_error == 1) {
        // Make button unclickable if Spotify is not available
        return;
    }
    current_capo_value = document.getElementById("IDguitarCapo");
    current_capo_value_int = parseInt(current_capo_value.innerHTML);
    if (current_capo_value_int < 12) {
        current_capo_value_int += 1;
        current_capo_value.innerHTML = current_capo_value_int;
        capo_plus_button.style.opacity = "1";
        capo_minus_button.style.opacity = "1";

        // Apply chord transpose (plus 1 capo) for main_chords_body
        var parser = new DOMParser();
        var parsed_body = parser.parseFromString(document.getElementById('IDdivMainChords').innerHTML, "text/html");
        var all_chords = parsed_body.getElementsByClassName("chord_span");
        for (let i = 0; i < all_chords.length; i++) {
            all_chords[i].innerHTML = sharOrFlatTranposer(transposeChord(all_chords[i].innerHTML.toString(), -1), current_flat_or_sharp);
        }
        document.getElementById('IDdivMainChords').innerHTML = parsed_body.body.innerHTML;
        main_chords_body = parsed_body.body.innerHTML;
    }

    if (current_capo_value_int == 12) {
        capo_plus_button.style.opacity = "0.5";
        capo_minus_button.style.opacity = "1";
    }
    if (initial_capo_value == current_capo_value_int) {
        current_capo_value.style.fontWeight = "bold";
        current_capo_value.style.color = "#1DB954";
    } else {
        current_capo_value.style.fontWeight = "normal";
        current_capo_value.style.color = "#1DB954";
    }

    // Check current_flat_or_sharp after capo change
    var parser3 = new DOMParser();
    var parsed_body_3 = parser3.parseFromString(document.getElementById('IDdivMainChords').innerHTML, "text/html");
    var all_chords_3 = parsed_body_3.getElementsByClassName("chord_span");
    amount_of_flats = 0;
    amount_of_sharps = 0;
    for (let i = 0; i < all_chords_3.length; i++) {
        amount_of_flats += (all_chords_3[i].innerHTML.match(/b/g) || []).length;
    }
    for (let i = 0; i < all_chords_3.length; i++) {
        amount_of_sharps += (all_chords_3[i].innerHTML.match(/#/g) || []).length;
    }
    if (amount_of_sharps > amount_of_flats) {
        document.getElementById("IDsharpSymbol").style.fontWeight = "bold";
        document.getElementById("IDsharpSymbol").style.color = "#1DB954";
        current_flat_or_sharp = "#";
    }
    if (amount_of_flats > amount_of_sharps) {
        document.getElementById("IDflatSymbol").style.fontWeight = "bold";
        document.getElementById("IDflatSymbol").style.color = "#1DB954";
        current_flat_or_sharp = "b";
    }
    if (amount_of_sharps == amount_of_flats) {
        document.getElementById("IDsharpSymbol").style.fontWeight = "normal";
        document.getElementById("IDsharpSymbol").style.color = "white";
        document.getElementById("IDflatSymbol").style.fontWeight = "normal";
        document.getElementById("IDflatSymbol").style.color = "white";
        // Do not reasign current_flat_or_sharp to persist the previous value when changing capo afterwards again
    }
});


//////// CHORD TRANPOSE FUNCTIONALITY ////////
var note_step_sharp_array = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"];
var note_step_flat_array =  ["A", "Bb", "B", "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab"];

function sharOrFlatTranposer(any_chord, sharp_or_flat) {
    if (sharp_or_flat == "#") return any_chord
    if (sharp_or_flat == "0") return any_chord
    
    var chord = any_chord;
    const sharp_notes = ["C#", "D#", "F#", "G#", "A#"];
    const flat_notes = ["Db", "Eb", "Gb", "Ab", "Bb"];
    
    for (let i = 0; i < sharp_notes.length; i++) {
        if (chord.includes(sharp_notes[i])) {
            chord = chord.replace(sharp_notes[i], flat_notes[i]);
        }
    }
    return chord;
}

function transposeChord(chord, n) {
    // Similar to "hammar"s Haskell approach
    // https://codegolf.stackexchange.com/questions/3847/create-a-function-for-transposing-musical-chords
    const notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    const sharp_notes = ["C#", "D#", "F#", "G#", "A#"];
    const flat_notes = ["Db", "Eb", "Gb", "Ab", "Bb"];

    for (let i = 0; i < flat_notes.length; i++) {
        if (chord.includes(flat_notes[i])) {
            chord = chord.replace(flat_notes[i], sharp_notes[i]);
        }
    }
    const chord_array = chord.split('/');
    const base_chord = chord_array[0];
    const slash_chord = chord_array[1];

    const transposed_base_chord = base_chord.replace(/[CDEFGAB]#?/g, match => {
        const index = (notes.indexOf(match) + n) % 12;
        if (index < 0) return notes[index + 12];
        return notes[index];
    });

    if (slash_chord) {
        const transposed_slash_chord = slash_chord.replace(/[CDEFGAB]#?/g, match => {
            const index = (notes.indexOf(match) + n) % 12;
            if (index < 0) return notes[index + 12];
            return notes[index];
        });
        return transposed_base_chord + '/' + transposed_slash_chord;
    }
    return transposed_base_chord;
}
// console.log(sharOrFlatTranposer(transposeChord("Cmaj7b5", 1), "#"));


//////// FLAT/SHARP BUTTON ////////
var flat_or_sharp_button = document.getElementById("IDflatOrSharp");
flat_or_sharp_button.addEventListener("click", () => {
    if (spotify_error == 1) {
        // Make button unclickable if Spotify is not available
        return;
    }
    sharp_symobl = document.getElementById("IDsharpSymbol");
    flat_symbol = document.getElementById("IDflatSymbol");
    if ((sharp_symobl.style.color == "white") && (flat_symbol.style.color == "white")) {
        return;
    }
    if (current_flat_or_sharp == "#") {
        current_flat_or_sharp = "b";

        var parser = new DOMParser();
        var parsed_body = parser.parseFromString(document.getElementById('IDdivMainChords').innerHTML, "text/html");
        var all_chords = parsed_body.getElementsByClassName("chord_span");
        for (let i = 0; i < all_chords.length; i++) {
            all_chords[i].innerHTML = sharOrFlatTranposer(transposeChord(all_chords[i].innerHTML.toString(), 0), current_flat_or_sharp);
        }
        document.getElementById('IDdivMainChords').innerHTML = parsed_body.body.innerHTML;
        main_chords_body = parsed_body.body.innerHTML;

        document.getElementById("IDsharpSymbol").style.fontWeight = "normal";
        document.getElementById("IDsharpSymbol").style.color = "white";    
        document.getElementById("IDflatSymbol").style.fontWeight = "bold";
        document.getElementById("IDflatSymbol").style.color = "#1DB954";
        
    } else if (current_flat_or_sharp == "b") {
        current_flat_or_sharp = "#";

        var parser = new DOMParser();
        var parsed_body = parser.parseFromString(document.getElementById('IDdivMainChords').innerHTML, "text/html");
        var all_chords = parsed_body.getElementsByClassName("chord_span");
        for (let i = 0; i < all_chords.length; i++) {
            all_chords[i].innerHTML = sharOrFlatTranposer(transposeChord(all_chords[i].innerHTML.toString(), 0), current_flat_or_sharp);
        }
        document.getElementById('IDdivMainChords').innerHTML = parsed_body.body.innerHTML;
        main_chords_body = parsed_body.body.innerHTML;

        document.getElementById("IDsharpSymbol").style.fontWeight = "bold";
        document.getElementById("IDsharpSymbol").style.color = "#1DB954";    
        document.getElementById("IDflatSymbol").style.fontWeight = "normal";
        document.getElementById("IDflatSymbol").style.color = "white";
    }
});


//////// SPOTIFY MUSIC CONTROL BUTTONS ////////
// Next Song
var next_spotify_track_button = document.getElementById("IDforwardButton");
next_spotify_track_button.addEventListener("click", () => {
    socket.emit('nextSpotifyTrack');
});
next_spotify_track_button.addEventListener("mouseover", () => {
    if (!is_on_touch_device) {
        next_spotify_track_button.style.opacity = "1";
    }
});
next_spotify_track_button.addEventListener("mouseout", () => {
    next_spotify_track_button.style.opacity = "0.7";
});

// Previous Song
var previous_spotify_track_button = document.getElementById("IDbackButton");
previous_spotify_track_button.addEventListener("click", () => {
    socket.emit('previousSpotifyTrack');
});
previous_spotify_track_button.addEventListener("mouseover", () => {
    if (!is_on_touch_device) {
        previous_spotify_track_button.style.opacity = "1";
    }
});
previous_spotify_track_button.addEventListener("mouseout", () => {
    previous_spotify_track_button.style.opacity = "0.7";
});

// Play/Pause Song
var play_pause_spotify_track_button = document.getElementById("IDplayAndPauseButton");
play_pause_spotify_track_button.addEventListener("click", () => {
    socket.emit('playPauseSpotifyTrack');
});
play_pause_spotify_track_button.addEventListener("mouseover", () => {
    if (!is_on_touch_device) {
        play_pause_spotify_track_button.style.scale = "1.1";
    }
});
play_pause_spotify_track_button.addEventListener("mouseout", () => {
    play_pause_spotify_track_button.style.scale = "1";
});


//////// TRACK TIMELINE ////////
var line_empty = document.getElementById('IDtimeLineEmpty');
var line_filled = document.getElementById('IDtimeLineFilled');
var line_empty_2 = document.getElementById('IDtimeLineEmpty2');
var line_filled_2 = document.getElementById('IDtimeLineFilled2');

// Display a second timeline at hover and hide real timeline to prevent backend updating conflict
line_empty.addEventListener("mousemove", (event) => {
    line_empty.style.visibility = "hidden";
    line_filled.style.visibility = "hidden";
    line_empty.style.display = "none";
    line_filled.style.display = "none";
    line_empty_2.style.visibility = "visible";
    line_filled_2.style.visibility = "visible";
    line_empty_2.style.display = "block";
    line_filled_2.style.display = "block";
    
    let timeline_width = line_empty_2.clientWidth;
    let clickX = event.clientX - line_empty_2.getBoundingClientRect().left;

    let quotient = clickX / timeline_width;
    let calc_ms = Math.round(quotient * track_duration_ms);

    let progress_ratio = calc_ms / track_duration_ms;
    let progress_percent = Math.round(progress_ratio * 100);
    line_filled_2.style.width = progress_percent + "%";
});

// Update second timeline at hover and update current track time
line_empty_2.addEventListener("mousemove", (event) => {
    currently_hovering_timeline = true;
    if (!is_on_touch_device) {
        line_empty_2.style.transform = "scaleY(2)";
        line_filled_2.style.backgroundColor = "#34df70";
    }
    line_empty.style.visibility = "hidden";
    line_filled.style.visibility = "hidden";
    line_empty.style.display = "none";
    line_filled.style.display = "none";
    line_empty_2.style.visibility = "visible";
    line_filled_2.style.visibility = "visible";
    line_empty_2.style.display = "block";
    line_filled_2.style.display = "block";

    let timeline_width = line_empty_2.clientWidth;
    let clickX = event.clientX - line_empty_2.getBoundingClientRect().left;

    let quotient = clickX / timeline_width;
    let calc_ms = Math.round(quotient * track_duration_ms);

    let currentTime = document.getElementById("IDcurrentTime");
    let totalSeconds = Math.floor(calc_ms / 1000);
    let minutes = Math.floor(totalSeconds / 60);
    let seconds = totalSeconds % 60;
    let formattedMinutes = minutes.toString();
    let formattedSeconds = seconds < 10 ? `0${seconds}` : seconds.toString();
    currentTime.textContent = formattedMinutes + ":" + formattedSeconds;

    let progress_ratio = calc_ms / track_duration_ms;
    let progress_percent = Math.round(progress_ratio * 100);
    line_filled_2.style.width = progress_percent + "%";
});

// Hide second timeline at hover-end and show real timeline again
line_empty_2.addEventListener("mouseleave", () => {
    currently_hovering_timeline = false;
    line_empty.style.visibility = "visible";
    line_filled.style.visibility = "visible";
    line_empty.style.display = "block";
    line_filled.style.display = "block";

    line_empty_2.style.visibility = "hidden";
    line_filled_2.style.visibility = "hidden";
    line_empty_2.style.display = "none";
    line_filled_2.style.display = "none";
});

// Click on second timeline -> Display line into center and send no time to backend
line_empty_2.addEventListener("click", (event) => {
    if (spotify_error == 1) {
        // Make button unclickable if Spotify is not available
        return;
    }
    if (musixmatch_lyrics_is_linesynced == 1) {
        dynamic_scroll = true;
    }
    clicked_on_timeline = true;
    let timeline_width = line_empty_2.clientWidth;
    let clickX = event.clientX - line_empty_2.getBoundingClientRect().left;

    let quotient = clickX / timeline_width;
    let calc_ms = Math.round(quotient * track_duration_ms);

    // Scroll immediately to the closest synced line available without waiting for server response or dynamic script
    // Important, as when clicking in timelime, you might click a time "between" existing timestamps and the dynamic script will 
    // scroll delayed only as soon as the next timestamp is the same as current time
    let closest_timestamp = null;
    let closest_difference = Infinity;
    clickable_synced_lines_timestamp_array.forEach((timestamp) => {
        let difference = Math.abs(timestamp - calc_ms);
        if (difference < closest_difference) {
            closest_difference = difference;
            closest_timestamp = timestamp;
        }
    });
    if (closest_timestamp != null) {
        current_synced_line = document.getElementById("IS_SYNCED_AT:" + closest_timestamp);
        try {
            current_synced_line.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
                inline: 'center'
            });
            current_synced_line.scrollTo;
        } catch {
            console.log('%cNo current synced line available - Could not center current line', 'color: yellow; font-weight: bold;');
        }
    }

    let progress_ratio = calc_ms / track_duration_ms;
    let progress_percent = Math.round(progress_ratio * 100);
    line_filled_2.style.width = progress_percent + "%";
    line_filled.style.width = progress_percent + "%";

    socket.emit('jumpInsideTrack', calc_ms);

    // Prevent dynamic script from updating to Spotifys current time until new one in front end is received
    sleepPromise(500).then(() => { clicked_on_timeline = false; });
});


//////// SYNC BUTTON ////////
var sync_button = document.getElementById("IDsyncButton");
var sync_button_current_rotation = 0;

// Hover effects
sync_button.addEventListener('mouseover', () =>  {
    if (!is_on_touch_device) {
        sync_button.style.transform = 'scale(0.85)'
    }
});
sync_button.addEventListener('mouseout', () =>  {
    if (!is_on_touch_device) {
        sync_button.style.transform = 'scale(1.0)'
    }
});

// Center synced line into view
sync_button.addEventListener('click', () =>  {
    if (spotify_error == 1 || complete_source_code_found == 0) {
        // Make button unclickable if Spotify is not available or no chords avaiable (stay at unsync)
        return;
    }
    try {
        current_synced_line.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'center'
        });
        current_synced_line.scrollTo;
    } catch {
        console.log('%cNo current synced line available - Could not center current line', 'color: yellow; font-weight: bold;');
    }

    dynamic_scroll = !dynamic_scroll;
    if (!dynamic_scroll) {
        sync_button.src = "static/sync_button.png";
        sync_button.style.opacity = "0.5";
    }

    if (dynamic_scroll) {
        sync_button.src = "static/sync_button_blue.png";
        sync_button.style.opacity = "1";
    }
});






