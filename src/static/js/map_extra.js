async function zoomToSourceCollection(source) {
    let d = await map.getSource(source).getData();
    let bounds = d.features.reduce((bounds, f) => {
        return bounds.extend(getFeatureBounds(f));
    }, new maplibregl.LngLatBounds(getFeatureBounds(features[0]), getFeatureBounds(features[0])));

    map.fitBounds(bounds, {
        padding: 20
    });
}

async function zoomToSource(source) {
    let d = await map.getSource(source).getData();

    const coordinates = getFlatCoords(d.features[0].geometry);

    // Pass the first coordinates in the LineString to `lngLatBounds` &
    // wrap each coordinate pair in `extend` to include them in the bounds
    // result. A variation of this technique could be applied to zooming
    // to the bounds of multiple Points or Polygon geometries - it just
    // requires wrapping all the coordinates with the extend method.
    let bounds = coordinates.reduce((bounds, coord) => {
        return bounds.extend(coord);
    }, new maplibregl.LngLatBounds(coordinates[0], coordinates[0]));

    map.fitBounds(bounds, {
        padding: 20
    });
}

async function zoomToSourcesOneFeature() {
    var promises = []
    var coords = []
    let src_arr = Object.keys(layerSourceMap);
    if (src_arr.length == 0) {
        return;
    }
    for (let i = 0; i < src_arr.length; i++) {
        let k = src_arr[i];
        let src = map.getSource(k)
        promises.push(src.getData());
    }

    let res = await Promise.all(promises)
    for (let r of res) {
        coords = coords.concat(getFlatCoords(r.features[0].geometry))
    }
    ;

    let bounds = coords.reduce((bounds, coord) => {
        return bounds.extend(coord);
    }, new maplibregl.LngLatBounds(coords[0], coords[0]));
    map.fitBounds(bounds, {
        padding: 20
    });
}

function rgb256ToHex(red, green, blue) {
    let rgb = blue | (green << 8) | (red << 16);
    return '#' + rgb.toString(16).padStart(6, '0');
}