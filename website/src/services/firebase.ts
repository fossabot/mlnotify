import type Firebase from 'firebase/app'


let _firebase: typeof Firebase
export const firebaseMessagingService = {
	async getFirebase(): Promise<typeof Firebase> {
		if(!_firebase){
			// We're importing it dynamically since firebase does not support bundling in a non-web environment
			// See https://github.com/firebase/firebase-js-sdk/issues/2222
			const [firebase] = await Promise.all([import('firebase/app'), import('firebase/messaging')])
			_firebase = firebase.default
		}

		return _firebase
	},
	async subscribeToTraining(
		messaging: Firebase.messaging.Messaging,
		serviceWorkerRegistration: ServiceWorkerRegistration,
	): Promise<string> {
		const currentToken = await messaging.getToken({ serviceWorkerRegistration })

		if (!currentToken) {
			throw new Error('No registration token available. Request permission to generate one.')
		}

		return currentToken
	},
	async initializeFirebaseMessaging(): Promise<Firebase.messaging.Messaging> {
		const firebase = await firebaseMessagingService.getFirebase()

		if (process.env.GRIDSOME_FIREBASE_APP_CONFIG) {
			firebase.initializeApp(JSON.parse(process.env.GRIDSOME_FIREBASE_APP_CONFIG))
		} else {
			throw new Error('No Firebase app config found')
		}

		const messaging = firebase.messaging()
		messaging.onMessage((payload: any) => {
			console.log('Message received. ', payload)
		})

		return messaging
	},
	async init(serviceWorkerRegistration: ServiceWorkerRegistration): Promise<string> {
		const messaging = await firebaseMessagingService.initializeFirebaseMessaging()
		return await messaging.getToken({ serviceWorkerRegistration })
	},
}
