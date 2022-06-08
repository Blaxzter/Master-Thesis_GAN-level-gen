/*****************************************************************************
** ANGRYBIRDS AI AGENT FRAMEWORK
** Copyright (c) 2014,XiaoYu (Gary) Ge, Stephen Gould,Jochen Renz
**  Sahan Abeyasinghe, Jim Keys,   Andrew Wang, Peng Zhang
** All rights reserved.
**This work is licensed under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
**To view a copy of this license, visit http://www.gnu.org/licenses/
*****************************************************************************/

package ab.utils;

import ab.server.Proxy;
import ab.server.proxy.message.ProxyGameStateMessage;
import ab.server.proxy.message.ProxyScoreMessage;
import ab.vision.GameStateExtractor.GameState;

public class StateUtil {
	/**
	 * Get the current game state
	 * 
	 * @return GameState: the current state
	 */
	public static GameState getGameState(Proxy proxy) {
		// byte[] imageBytes = proxy.send(new ProxyScreenshotMessage());
		//
		// BufferedImage image = null;
		// try {
		// image = ImageIO.read(new ByteArrayInputStream(imageBytes));
		// } catch (IOException e) {
		//
		// }

		// GameStateExtractor gameStateExtractor = new GameStateExtractor();
		// GameStateExtractor.GameState state =
		// gameStateExtractor.getGameState(image);

		GameState state = proxy.send(new ProxyGameStateMessage());
		return state;
	}

	private static int _getScore(Proxy proxy) {
		// byte[] imageBytes = proxy.send(new ProxyScreenshotMessage());
		int score = -1;
		//
		// BufferedImage image = null;
		// try {
		// image = ImageIO.read(new ByteArrayInputStream(imageBytes));
		// }
		// catch (IOException e) {
		// e.printStackTrace();
		// }

		// GameStateExtractor gameStateExtractor = new GameStateExtractor();
		// GameState state = gameStateExtractor.getGameState(image);

		GameState state = proxy.send(new ProxyGameStateMessage());

		if (state == GameState.PLAYING)
			score = proxy.send(new ProxyScoreMessage());
		else if (state == GameState.WON)
			score = proxy.send(new ProxyScoreMessage());

		if (score == -1)
			System.out.println(" Game score is unavailable ");
		return score;
	}

	/**
	 * The method checks the score every second, and return when the score is
	 * stable (not flashing).
	 * 
	 * @return score: the current score.
	 * 
	 */
	public static int getScore(Proxy proxy) {

		int current_score = -1;
		while (current_score != _getScore(proxy)) {
			try {
				Thread.sleep(1000);
			} catch (InterruptedException e) {

				e.printStackTrace();
			}
			if (getGameState(proxy) == GameState.WON) {
				current_score = _getScore(proxy);
			} else
				System.out.println(" Unexpected state: PLAYING");
		}
		return current_score;
	}

}
