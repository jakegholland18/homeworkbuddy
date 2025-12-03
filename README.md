# CozmicLearning

## Development Notes

### JSON endpoints and cookies
Teacher dashboard uses JSON endpoints that rely on session cookies for authentication. When calling these endpoints from the browser, ensure fetch includes credentials so cookies are sent:

```js
fetch('/teacher/assign_questions', {
	method: 'POST',
	headers: { 'Content-Type': 'application/json' },
	credentials: 'same-origin',
	body: JSON.stringify(payload)
})
```

This applies to preview, assign, lesson plan, Teacher's Pet, analytics, and report routes. Many JSON endpoints are CSRF-exempt server-side, but they still require the session cookie to be present.
