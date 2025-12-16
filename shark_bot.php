<?php

require_once 'shark_api.php';

class SharkTelegramBot {
    private $token;
    private $api_url = 'https://api.telegram.org/bot';
    
    public function __construct($token) {
        $this->token = $token;
    }
    
    public function processUpdate($update) {
        if (isset($update['message'])) {
            $message = $update['message'];
            $chat_id = $message['chat']['id'];
            $text = $message['text'] ?? '';
            
            if (strpos($text, '/start') === 0) {
                $this->sendMessage($chat_id, "🦈 SHARK Bot\nSend me a link to download!");
            } elseif (strpos($text, '/help') === 0) {
                $this->sendMessage($chat_id, "Help: Send Instagram/YouTube/Twitter/TikTok links");
            } elseif (filter_var($text, FILTER_VALIDATE_URL)) {
                $this->handleLink($chat_id, $text);
            } else {
                $this->sendMessage($chat_id, "Send a valid URL");
            }
        }
    }
    
    private function handleLink($chat_id, $url) {
        $this->sendMessage($chat_id, "🔍 Processing...");
        
        $data = ['url' => $url];
        $result = $this->callApi($data);
        
        if ($result['status'] === 'success') {
            $platform = $result['platform'];
            $message = "✅ {$platform} detected!\n";
            
            $keyboard = [
                'inline_keyboard' => [
                    [
                        ['text' => '📥 Download HD', 'callback_data' => "dl_{$platform}_hd"],
                        ['text' => '🎵 Audio', 'callback_data' => "dl_{$platform}_audio"]
                    ]
                ]
            ];
            
            $this->sendMessage($chat_id, $message, $keyboard);
        } else {
            $this->sendMessage($chat_id, "❌ Error: " . $result['message']);
        }
    }
    
    private function callApi($data) {
        $ch = curl_init('http://localhost/shark_api.php');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        
        $response = curl_exec($ch);
        curl_close($ch);
        
        return json_decode($response, true);
    }
    
    private function sendMessage($chat_id, $text, $reply_markup = null) {
        $url = $this->api_url . $this->token . '/sendMessage';
        $data = [
            'chat_id' => $chat_id,
            'text' => $text,
            'parse_mode' => 'HTML'
        ];
        
        if ($reply_markup) {
            $data['reply_markup'] = json_encode($reply_markup);
        }
        
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
        curl_exec($ch);
        curl_close($ch);
    }
}

$bot_token = 'YOUR_BOT_TOKEN';
$bot = new SharkTelegramBot($bot_token);

$update = json_decode(file_get_contents('php://input'), true);
if ($update) {
    $bot->processUpdate($update);
}
?>
