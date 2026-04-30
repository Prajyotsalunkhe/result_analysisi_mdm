const admin = require('firebase-admin');

// This logic prevents re-initializing the app if it's already running
if (!admin.apps.length) {
    admin.initializeApp({
        credential: admin.credential.cert({
            projectId: process.env.FIREBASE_PROJECT_ID,
            clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
            // The replace() fix ensures newlines from Netlify are handled correctly
            privateKey: process.env.FIREBASE_PRIVATE_KEY.replace(/\\n/g, '\n'),
        }),
    });
}

const db = admin.firestore();
// Now you can export 'db' or other services to use in your functions
exports.handler = async function (event, context) {
    return {
        statusCode: 200,
        body: JSON.stringify({ message: "Firebase Admin is initialized" }),
    };
};