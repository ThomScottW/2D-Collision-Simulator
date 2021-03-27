import pygame
import math    # For trigonometry.
import random  # For random generation of particles and their attributes.


# Simulation Constants
NUM_PARTICLES = 10
ELASTICITY_COEFFICIENT = 0.8
DRAG_COEFFICIENT = 0.9999
MOUSE_FLING_COEFFICIENT = 0.1


class Vector:
    """A 2D vector whose x and y components correspond to the x and y
    components of a particle's velocity, respectively."""

    def __init__(self, x, y):
        self._x_comp = x
        self._y_comp = y

    def x(self) -> int or float:
        return self._x_comp

    def y(self) -> int or float:
        return self._y_comp

    def unit(self):
        """Return a unit vector with the same direction as this one."""
        return Vector(
            self._x_comp / self.magnitude(),
            self._y_comp / self.magnitude()
        )

    def magnitude(self):
        """Return this vector's magnitude."""
        return math.hypot(self._x_comp, self._y_comp)

    def __mul__(self, right):
        """Overload multiplication to perform the dot product operation if
        between two vectors, otherwise multiply the components by a provided factor."""
        if type(right) == Vector:
            return (self._x_comp * right._x_comp) + (self._y_comp * right._y_comp)
        elif type(right) in (int, float):
            return Vector(self._x_comp * right, self._y_comp * right)
        else:
            raise NotImplemented(f"Multiplication not supported between Vector and {type(right)}.")

    def __add__(self, right):
        if type(right) != Vector:
            raise NotImplemented(f"Addition not supported between Vector and {type(right)}")
        else:
            return Vector(self._x_comp + right._x_comp, self._y_comp + right._y_comp)


class Particle:
    """A particle, represented by a circle."""

    def __init__(
        self,
        position: (int, int),
        mass: int,
        radius: int,
        speed: float,
        angle: float,
        color: (int, int, int)
    ):
        self._x, self._y = position
        self._color = color
        self._mass = mass
        self._radius = radius
        # Attributes related to movement.
        self._speed_x = math.cos(angle) * speed
        self._speed_y = math.sin(angle) * speed
        self._speed = speed
        self._angle = angle

    # These three member functions are for use with the click-and-drag functionality.
    def x(self) -> float:
        return self._x

    def y(self) -> float:
        return self._y

    def radius(self) -> int:
        return self._radius

    def display(self, surface: pygame.Surface):
        """Draw a circle representing this particle on the display."""
        pygame.draw.circle(
            surface,
            self._color,
            # Math.floor ensures integer arguments are given. This pygame function
            # only accepts integers.
            (math.floor(self._x), math.floor(self._y)),
            self._radius
        )

    def move(self, surface: pygame.Surface) -> None:
        """Move the particle in the direction it's pointing."""
        self._x += self._speed_x
        self._y += self._speed_y
        self._bounce(surface)
        self._apply_drag()

    def follow(self, mouse_coodinates: (int, int)) -> None:
        """Change the particle's vector to point towards the mouse cursor."""
        dx = mouse_coodinates[0] - self._x
        dy = mouse_coodinates[1] - self._y
        # Calculate a new speed for the particle based on the distance between the
        # two points.
        self._speed = math.hypot(dx, dy)
        # Math.atan2(dy, dx) will calculate the particle's new direction, which will
        # be pointing towards the mouse cursor's coordinates.
        self._recalculate_speed_components(math.atan2(dy, dx), MOUSE_FLING_COEFFICIENT)
        # Multiplying by MOUSE_FLING_COEFFICIENT slows down the particle enough to let
        # the mouse cursor get ahead, and enables a realistic-looking flinging effect.

    def collide(self, p2) -> None:
        """Resolve a collision with another particle p2."""
        if self._is_colliding(p2):
            # When two particles collide, there are two "vectors" that represent
            # the collision: a tangential vector, which is tangent to the two
            # particles; and a normal vector, which goes through the centers of
            # the particles.

            # The particles do not move in the tangential direction, only the normal direction.
            # To find a normal vector, we simply have a vector whose components are the differences
            # between the coordinates of the two colliding particles.
            n_vec = Vector(self._x - p2._x, self._y - p2._y)

            # The tangent vector's x component is the negative of the normal
            # vector's y, and its y is the normal's x.
            t_vec = Vector(-n_vec.y(), n_vec.x())

            # We also need unit vectors corresponding to the previous two, so
            # that we can project the particles's vectors onto the unit vectors
            # and calculate final velocity vectors.
            unit_n_vec = n_vec.unit()
            unit_t_vec = t_vec.unit()

            # Now we need vectors corresponding to the two particles' speeds.
            p1_initial_vec = Vector(self._speed_x, self._speed_y)
            p2_initial_vec = Vector(p2._speed_x, p2._speed_y)

            # Now we use the dot product of each particle's velocity vectors
            # with the unit vectors to find the tangential and normal components
            # of each vector's velocity.
            #
            # Remember that the tangential components of each vector's velocity
            # does not change, so there are no "initial" tangential components.
            p1_initial_norm_comp = p1_initial_vec * unit_n_vec
            p1_tan_comp = p1_initial_vec * unit_t_vec

            p2_initial_norm_comp = p2_initial_vec * unit_n_vec
            p2_tan_comp = p2_initial_vec * unit_t_vec

            # Now that we've projected each particle's velocity vector onto the
            # unit normal vectors, we can use Newton's 1-dimensional collision
            # equation to calculate the final normal components of each particle's
            # velocity.
            p1_final_norm_comp = ( (p1_initial_norm_comp * (self._mass - p2._mass)
                                    + 2 * p2._mass * p2_initial_norm_comp) 
                                    / (self._mass + p2._mass) )

            p2_final_norm_comp = ( (p2_initial_norm_comp * (p2._mass - self._mass)
                                    + 2 * self._mass * p1_initial_norm_comp)
                                    / (self._mass + p2._mass) )

            # Now that we have the final normal components of each velocity, we
            # multiply them by the unit normal vector to get the final normal vectors
            # for each particle.
            p1_final_n_vec = unit_n_vec * p1_final_norm_comp
            p2_final_n_vec = unit_n_vec * p2_final_norm_comp
            # Do the same for the tangential vectors, which didn't change.
            p1_final_t_vec = unit_t_vec * p1_tan_comp
            p2_final_t_vec = unit_t_vec * p2_tan_comp

            # Now we add the normal and tangential vectors for each particle together
            # to get their final complete vectors.
            p1_final_vec = p1_final_n_vec + p1_final_t_vec
            p2_final_vec = p2_final_n_vec + p2_final_t_vec

            # Now we have to change this vector form of velocity into an angle and
            # speed that we can use to move the particle around using our move function.
            self._speed = p1_final_vec.magnitude()
            self._angle = math.atan2(p1_final_vec.y(), p1_final_vec.x())
            self._recalculate_speed_components(self._angle)

            # Do the same for p2.
            p2._speed = p2_final_vec.magnitude()
            p2._angle = math.atan2(p2_final_vec.y(), p2_final_vec.x())
            p2._recalculate_speed_components(p2._angle)

            # Apply elasticity to both particles to simulate the loss of energy
            # during the collision.
            self._apply_elasticity()
            p2._apply_elasticity()

            # Because this is a discrete simulation, we need to push the particles apart
            # by the distance that they overlap, this is to prevent the particles from
            # sticking to each other if they overlap between frames.
            self._push_apart(p2)

    def _push_apart(self, p2) -> None:
        """Push this particle and p2 apart by the distance that they overlap."""
        # To find the amount of overlap, we subtract the distance between
        # the particles from the sum of their radiuses.
        dist = self._overlap_amount(p2)

        # Then we need the angle of collision.
        collision_angle = math.atan2(self._y - p2._y, self._x - p2._x)

        # Now we need to update the x and y positions of each particle accordingly.
        self._x += math.cos(collision_angle) * dist
        self._y += math.sin(collision_angle) * dist
        p2._x -= math.cos(collision_angle) * dist
        p2._y -= math.sin(collision_angle) * dist

    def _overlap_amount(self, p2) -> float:
        """Return the amount of overlap between two particles."""
        x_dif = self._x - p2._x
        y_dif = self._y - p2._y
        return (self._radius + p2._radius) - math.hypot(x_dif, y_dif)

    def _is_colliding(self, p2) -> bool:
        """Return True if the distance between the particles is less than the
        sum of their radiuses, otherwise return False."""
        return self._overlap_amount(p2) > 0

    def _bounce(self, surface: pygame.Surface) -> None:
        """Bounce off the edge of the display."""
        width, height = surface.get_size()
        # Top-of-window collision.
        if self._y <= self._radius:
            # Update angle to deflect off of surface.
            self._recalculate_speed_components(-self._angle)
            # Update position to prevent an out-of-bounds situation.
            # This is necessary because this is a discrete simulation, and
            # the particle can be in bounds on frame, and out the next, so we have
            # to update the position to make it look like the particle just bounced
            # off the surface.

            # We add here because we're deflecting off of the top, and the y-axis is
            # flipped such that to go downwards, we add -- and subtract for going
            # upwards.
            self._y += 2 * (self._radius - self._y)
        # Bottom-of-window collision.
        elif self._y >= (height - self._radius):
            self._recalculate_speed_components(-self._angle)
            self._y -= 2 * (self._y + self._radius - height)
        # Left-of-window collision.
        elif self._x <= self._radius:
            self._recalculate_speed_components(math.pi - self._angle)
            self._x += 2 * (self._radius - self._x)
        # Right-of-window collision.
        elif self._x >= width - self._radius:
            self._recalculate_speed_components(math.pi - self._angle)
            self._x -= 2 * (self._x + self._radius - width)
        else:
            # If we didn't bounce off of an edge, return early without
            # applying elasticity.
            return

        # Apply elasticity so the particle loses energy when it bounces.
        self._apply_elasticity()

    def _apply_drag(self) -> None:
        """Update the particle's speed to simulate the effect of drag."""
        self._recalculate_speed_components(self._angle, DRAG_COEFFICIENT)

    def _apply_elasticity(self) -> None:
        """Update the particle's speed to simulate the effect of elasticity."""
        self._recalculate_speed_components(self._angle, ELASTICITY_COEFFICIENT)

    def _recalculate_speed_components(self, new_angle: float, speed_coefficient=None) -> None:
        """Change the x and y components of speed depending on a new angle."""
        if speed_coefficient:
            self._speed *= speed_coefficient
        self._angle = new_angle
        self._speed_x = math.cos(new_angle) * self._speed
        self._speed_y = math.sin(new_angle) * self._speed


class Simulation:
    """This is the class responsible for controlling what happens in the
    pygame window."""

    def __init__(self):
        # Initialize Pygame.
        pygame.init()

        # Create a pygame window. This is what pops up when this file is run.
        self._width, self._height = 800, 800  # Width and height in pixels.
        # This will create the pygame window.
        self._surface = pygame.display.set_mode((self._width, self._height))
        # Fill the background with white and set a caption for the window.
        self._surface.fill((255, 255, 255))
        pygame.display.set_caption("2D Collisions")

        # Fill the window with randomly created particles.
        self._particles = self._generate_particles(NUM_PARTICLES)
        # This attribute determines whether or not we have selected a particle
        # by clicking on one, which lets us drag and throw it around.
        self._selected_particle = None

    def _generate_particles(self, num: int) -> [Particle]:
        """Generate num random particles."""
        particles = []
        for _ in range(num):
            # First, give the particle a radius.
            radius = random.randint(2, 20)
            # Then, determine a position for the particle, within the bounds of the window.
            pos_x = random.randint(radius, self._width - radius)
            pos_y = random.randint(radius, self._height - radius)
            # Now, determine an angle and speed for the particle.
            angle = random.uniform(0, 2 * math.pi)
            speed = random.random()
            # We can also calculate a "density" for the particle, which we can use
            # to shift the color of the particle and calculate a mass.
            density = random.randint(1, 20)
            # Create and append a particle to the list of particles.

            # The mass is calculated by re-arranging the formula for density (d = m/V),
            # except instead of volume we use area of a circle.

            # Additionally, the color is deterimined by subtracting the density * 10 from
            # 255 from the G and B values, which means that denser particles will be darker
            # than less dense ones.
            particles.append(Particle(
                (pos_x, pos_y),
                density * math.pi * (radius ** 2),
                radius,
                speed,
                angle,
                (255, 200 - density * 10, 200 - density * 10)
            ))
        return particles

    def run(self) -> None:
        """Run the simulation."""
        self._running = True

        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                # These next two events are for implementing
                # the selection (and dragging around) of a particle.
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Event.pos returns the coordinates of the mouse click.
                    self._select_particle(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self._deselect_particle()

            self._handle_events()
            self._redraw_frame()

    def _handle_events(self) -> bool:
        """Handle pygame and particle interactions."""
        if self._selected_particle:
            self._selected_particle.follow(pygame.mouse.get_pos())
        for index, particle in enumerate(self._particles):
            particle.move(self._surface)

            # Slicing the list of particles by index + 1 ensures that
            # each particle only collides with every other particle once by
            # only resolving collisions with particles that come after it in the list.
            for other_particle in self._particles[index + 1:]:
                particle.collide(other_particle)

    def _redraw_frame(self):
        """Redraw the background, the particles, and then flip the display."""
        self._surface.fill((255, 255, 255))

        for particle in self._particles:
            particle.display(self._surface)

        pygame.display.flip()

    def _select_particle(self, coords: (int, int)) -> None:
        """Select a particle if the mouse clicks on one."""
        for particle in self._particles:
            dx = coords[0] - particle.x()
            dy = coords[1] - particle.y()
            distance = math.hypot(dx, dy)
            # If the distance between the point where the mouse clicked
            # is less than the radius of the Particle, then we must have
            # clicked inside the particle, thus selecting it.
            if distance <= particle.radius():
                self._selected_particle = particle
                return

    def _deselect_particle(self) -> None:
        """Deselect a particle, if one is already selected. Do nothing otherwise."""
        if self._selected_particle:
            self._selected_particle = None


if __name__ == "__main__":
    Simulation().run()
