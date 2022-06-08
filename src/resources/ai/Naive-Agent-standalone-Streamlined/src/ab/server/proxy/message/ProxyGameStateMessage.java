package ab.server.proxy.message;

import org.json.simple.JSONObject;

import ab.server.ProxyMessage;
import ab.vision.GameStateExtractor.GameState;

public class ProxyGameStateMessage implements ProxyMessage<GameState> {

	@Override
	public String getMessageName() {
		return "gamestate";
	}

	@Override
	public JSONObject getJSON() {
		return new JSONObject();
	}

	@Override
	public GameState gotResponse(JSONObject data) {
		
		String gameState = (String) data.get("data");
		
		if(gameState.equals("MainMenu"))
			return GameState.MAIN_MENU;
		
		if(gameState.equals("LevelSelectMenu"))
			return GameState.LEVEL_SELECTION;
		
		if(gameState.equals("LoadingScene") || gameState.equals("SplashScreen"))
			return GameState.LOADING;
		
		if(gameState.equals("GameWorld"))
			return GameState.PLAYING;
		
		if(gameState.equals("LevelCleared"))
			return GameState.WON;
		
		if(gameState.equals("LevelFailed"))
			return GameState.LOST;
					
		return GameState.UNKNOWN;
	}
}
