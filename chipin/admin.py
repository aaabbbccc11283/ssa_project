                Stuff from group detail i got rid of

		<!-- Allow the comment owner or admin to edit or delete -->
		{% if comment.user == request.user or request.user == group.admin %}
                    <a href="{% url 'chipin:edit_comment' group.id comment.id %}">Edit</a>
                    <a href="{% url 'chipin:delete_comment' comment.id %}" onclick="return confirm('Are you sure?')">Delete</a>
                {% endif %}


    <!-- Only list Join Requests for groups of which the current user is a member. -->
    {% if request.user in group.members.all %}
        <h2>Join Requests</h2>
        <ul>
            {% for request in group.join_requests.all %}
                <li>{{ request.user.username }} has requested to join.</li>
                {% if request.user not in group.members.all and request.user != group.admin %}
                    <a href="{% url 'chipin:vote_on_join_request' group.id request.id 'approve' %}">Approve</a>
                    <a href="{% url 'chipin:vote_on_join_request' group.id request.id 'reject' %}">Reject</a>
                {% endif %}
            {% endfor %}
        </ul>
    {% endif %}


from home.html
    <h2>Your Join Requests</h2>
    <ul>
        {% for join_request in user_join_requests %}
        <li>
            You requested to join <strong>{{ join_request.group.name }}</strong> on {{ join_request.created_at }}.
            <a href="{% url 'chipin:delete_join_request' join_request.id %}" onclick="return confirm('Are you sure you want to delete this join request?');">Delete</a>
        </li>
        {% empty %}
        <li>You have not submitted any join requests.</li>
        {% endfor %}
    </ul>

    <h2>Available Groups to Join</h2>
    <ul>
        {% for group in available_groups %}
        <li>
            <a href="{% url 'chipin:group_detail' group.id %}">{{ group.name }}</a>
            <span>- Admin: {{ group.admin.profile.nickname }}</span>
        </li>
        {% empty %}
        <li>No groups available to join.</li>
        {% endfor %}
    </ul>