<?php

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

$response = ['status' => 'error', 'message' => 'Invalid request'];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (isset($input['url'])) {
        $url = trim($input['url']);
        
        if (filter_var($url, FILTER_VALIDATE_URL)) {
            $platform = detectPlatform($url);
            
            if ($platform) {
                $result = processDownload($url, $platform);
                $response = $result;
            } else {
                $response = ['status' => 'error', 'message' => 'Platform not supported'];
            }
        } else {
            $response = ['status' => 'error', 'message' => 'Invalid URL'];
        }
    }
} elseif ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (isset($_GET['action'])) {
        switch ($_GET['action']) {
            case 'status':
                $response = ['status' => 'online', 'version' => '10.0', 'time' => time()];
                break;
            case 'platforms':
                $response = [
                    'platforms' => ['instagram', 'youtube', 'twitter', 'tiktok', 'facebook', 'reddit']
                ];
                break;
        }
    }
}

echo json_encode($response);

function detectPlatform($url) {
    $patterns = [
        'instagram' => '/instagram\.com/i',
        'youtube' => '/(youtube\.com|youtu\.be)/i',
        'twitter' => '/(twitter\.com|x\.com)/i',
        'tiktok' => '/tiktok\.com/i',
        'facebook' => '/facebook\.com/i',
        'reddit' => '/reddit\.com/i'
    ];
    
    foreach ($patterns as $platform => $pattern) {
        if (preg_match($pattern, $url)) {
            return $platform;
        }
    }
    
    return false;
}

function processDownload($url, $platform) {
    $cache_file = 'cache/' . md5($url) . '.json';
    
    if (file_exists($cache_file) && (time() - filemtime($cache_file)) < 300) {
        return json_decode(file_get_contents($cache_file), true);
    }
    
    $result = ['status' => 'success', 'platform' => $platform, 'url' => $url];
    
    switch ($platform) {
        case 'instagram':
            $result['type'] = 'instagram_post';
            $result['media'] = ['url' => $url];
            break;
        case 'youtube':
            $result['type'] = 'youtube_video';
            $result['formats'] = ['720p', '480p', '360p', 'audio'];
            break;
        case 'twitter':
            $result['type'] = 'twitter_post';
            break;
        case 'tiktok':
            $result['type'] = 'tiktok_video';
            $result['watermark'] = false;
            break;
    }
    
    file_put_contents($cache_file, json_encode($result));
    
    return $result;
}
?>
