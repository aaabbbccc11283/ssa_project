                <!-- Allow the comment owner or admin to edit or delete -->
		{% if comment.user == request.user or request.user == group.admin %}
                    <a href="{% url 'chipin:edit_comment' group.id comment.id %}">Edit</a>
                    <a href="{% url 'chipin:delete_comment' comment.id %}" onclick="return confirm('Are you sure?')">Delete</a>
                {% endif %}