/*****************************************************************************
** ANGRYBIRDS AI AGENT FRAMEWORK
** Copyright (c) 2014,  XiaoYu (Gary) Ge, Stephen Gould, Jochen Renz
** Sahan Abeyasinghe , Jim Keys,  Andrew Wang, Peng Zhang
** All rights reserved.
**This work is licensed under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
**To view a copy of this license, visit http://www.gnu.org/licenses/
*****************************************************************************/
package ab.demo.other;

import ab.server.Proxy;
import ab.server.proxy.message.ProxyLevelSelectMessage;
import ab.server.proxy.message.ProxyLoadSceneMessage;
import ab.server.proxy.message.ProxyMouseWheelMessage;
import ab.utils.StateUtil;
import ab.vision.GameStateExtractor.GameState;

/**
 * Schema for loading level
 */
public class LoadLevelSchema {
	
	private Proxy proxy;
//	private boolean pageSwitch = false;

	public LoadLevelSchema(Proxy proxy) {
		this.proxy = proxy;
	}

	public boolean loadLevel(int i) {

//		if (i > 21) {
//			if (i == 22 || i == 43)
//				pageSwitch = true;
//
//			i = ((i % 21) == 0) ? 21 : i % 21;
//		}

		// System.out.println(StateUtil.checkCurrentState(proxy));
		loadLevel(StateUtil.getGameState(proxy), i);

		GameState state = StateUtil.getGameState(proxy);

		while (state != GameState.PLAYING) {
			
			System.out.println(" In state:   " + state + " Try reloading...");
			
			loadLevel(state, i);
			
			try {
				Thread.sleep(100);
			} catch (InterruptedException e1) {

				e1.printStackTrace();
			}

			state = StateUtil.getGameState(proxy);
		}
		
		return true;
	}

	private boolean loadLevel(GameState state, int i) {
		
		if(state == GameState.LOADING) {
			return false;
		}
		
		if (state == GameState.MAIN_MENU) {
			
			// Go to level selection
			ActionRobot.GoFromMainMenuToLevelSelection();
			
			try {
				Thread.sleep(100);
			} catch (InterruptedException e) {

				e.printStackTrace();
			}
			
			// Load the level
			proxy.send(new ProxyLevelSelectMessage(i));
		}
		else if (state == GameState.LEVEL_SELECTION || state == GameState.WON || state == GameState.LOST) {
			
			// Load the level
			proxy.send(new ProxyLevelSelectMessage(i));
		}
		else  {
			
			// Go to main menu
			proxy.send(new ProxyLoadSceneMessage("MainMenu"));

			try {
				Thread.sleep(100);
			} catch (InterruptedException e) {

				e.printStackTrace();
			}
			
			// Go to level selection
			ActionRobot.GoFromMainMenuToLevelSelection();
			
			try {
				Thread.sleep(100);
			} catch (InterruptedException e) {

				e.printStackTrace();
			}
			
			// Load the level
			proxy.send(new ProxyLevelSelectMessage(i));
		} 

		// Wait 9000 seconds for loading the level
		GameState _state = StateUtil.getGameState(proxy);

		// at most wait 10 seconds
		int count = 0;
		while (_state != GameState.PLAYING && count < 3) {

			try {
				Thread.sleep(100);
			} catch (InterruptedException e1) {

				e1.printStackTrace();
			}

			count++;
			_state = StateUtil.getGameState(proxy);
		}

		if (_state == GameState.PLAYING) {

			for (int k = 0; k < 1; k++) {
				proxy.send(new ProxyMouseWheelMessage(-1));
			}

			try {
				Thread.sleep(100);
			} catch (InterruptedException e1) {

				e1.printStackTrace();
			}
		}

		return true;
	}
}
